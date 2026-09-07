"""Google Sheets analytics sink.

`enqueue()` drops a row on an in-memory queue and returns immediately — the
handler that logged the event is never blocked and never sees an error from
here. A single background daemon thread does the actual gspread network calls.
If Sheets is unreachable the row is lost *here* only: every event is already
persisted to data/interactions.jsonl by src.events before this is called.

Inactive (no-op) unless both GOOGLE_SERVICE_ACCOUNT_JSON and
ANALYTICS_SPREADSHEET_ID are configured.
"""

from __future__ import annotations

import logging
import queue
import threading
from datetime import datetime, timezone
from pathlib import Path

from src.config import settings

logger = logging.getLogger("sheets")

COLUMNS = [
    "timestamp",
    "event",
    "user_id",
    "username",
    "name",
    "segment",
    "raw_param",
    "reason",
]

_MAX_QUEUE = 1000
_queue: "queue.Queue[dict[str, object]]" = queue.Queue(maxsize=_MAX_QUEUE)
_worker: threading.Thread | None = None
_worker_lock = threading.Lock()


def enqueue(
    event: str,
    *,
    user_id: object,
    username: object,
    name: object,
    segment: object,
    raw_param: object,
    reason: object,
) -> None:
    """Queue one analytics row. Non-blocking; safe to call from async code."""
    if not settings.analytics_enabled:
        return
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "event": event,
        "user_id": user_id,
        "username": username,
        "name": name,
        "segment": segment,
        "raw_param": raw_param,
        "reason": reason,
    }
    try:
        _queue.put_nowait(row)
    except queue.Full:
        logger.warning("sheets queue full — dropping analytics row (kept in JSONL)")
        return
    _ensure_worker()


def _ensure_worker() -> None:
    global _worker
    with _worker_lock:
        if _worker is None or not _worker.is_alive():
            _worker = threading.Thread(target=_run, name="sheets-sink", daemon=True)
            _worker.start()


def _run() -> None:
    try:
        worksheet = _open_worksheet()
    except Exception as error:  # noqa: BLE001 - never let the worker die noisily
        logger.warning("Google Sheets sink disabled — %s", _explain(error))
        _drain()
        return

    while True:
        row = _queue.get()
        values = [_cell(row.get(col)) for col in COLUMNS]
        for attempt in (1, 2):
            try:
                # Cheap guard: restores the header row if the sheet was cleared
                # while the bot was running (one extra read per event).
                _ensure_headers(worksheet)
                worksheet.append_row(values, value_input_option="RAW")
                break
            except Exception as error:  # noqa: BLE001
                if attempt == 2:
                    logger.warning(
                        "failed to append analytics row (%s): %s",
                        type(error).__name__,
                        error or repr(error),
                    )
                else:
                    threading.Event().wait(2.0)
        _queue.task_done()


def _sa_email() -> str | None:
    try:
        import json

        data = json.loads(
            Path(settings.google_service_account_json).read_text(encoding="utf-8")
        )
        return data.get("client_email")
    except Exception:  # noqa: BLE001
        return None


def _explain(error: Exception) -> str:
    """Turn a gspread/setup error into an actionable one-line message.

    Several gspread exceptions stringify to '' (e.g. SpreadsheetNotFound), so a
    bare "%s" logs nothing — hence the explicit handling here.
    """
    import gspread

    sheet_id = settings.analytics_spreadsheet_id
    sa = _sa_email() or "the service account's client_email"

    if isinstance(error, FileNotFoundError):
        return str(error)
    if isinstance(error, gspread.exceptions.SpreadsheetNotFound):
        return (
            f"spreadsheet {sheet_id!r} not found (404). Check ANALYTICS_SPREADSHEET_ID "
            f"(the token between /d/ and /edit in the sheet URL) and that the Google "
            f"Sheets API is enabled for this service account's Cloud project."
        )
    if isinstance(error, PermissionError):
        return f"access denied (403) — share the spreadsheet with {sa} as Editor."
    return f"{type(error).__name__}: {error or repr(error)}"


def _open_worksheet():
    import gspread  # imported lazily so the bot runs without the dependency

    key_path = Path(settings.google_service_account_json)
    if not key_path.is_file():
        raise FileNotFoundError(f"service account key not found: {key_path}")

    client = gspread.service_account(filename=str(key_path))
    spreadsheet = client.open_by_key(settings.analytics_spreadsheet_id)
    try:
        worksheet = spreadsheet.worksheet(settings.analytics_worksheet)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=settings.analytics_worksheet, rows=1000, cols=len(COLUMNS)
        )

    _ensure_headers(worksheet)
    logger.info(
        "Google Sheets sink ready: %s / %s",
        settings.analytics_spreadsheet_id,
        settings.analytics_worksheet,
    )
    return worksheet


def _ensure_headers(worksheet) -> None:
    """Write the header row if it is missing or wrong (e.g. sheet was cleared)."""
    if worksheet.row_values(1) != COLUMNS:
        worksheet.update([COLUMNS], "A1", value_input_option="RAW")
        logger.info("Google Sheets: (re)wrote header row")


def _drain() -> None:
    """Discard queued rows when the sink cannot start (data is safe in JSONL)."""
    try:
        while True:
            _queue.get_nowait()
            _queue.task_done()
    except queue.Empty:
        pass


def _cell(value: object) -> object:
    return "" if value is None else value


def _summary_formula() -> str:
    """A ready-to-paste QUERY that pivots the raw events by segment."""
    src = f"'{settings.analytics_worksheet}'!A2:H"
    return (
        f'=QUERY({src}, "select F, count(B), '
        "sum(if(B='magnet_delivered',1,0)), sum(if(B='handoff',1,0)) "
        "where B is not null group by F "
        "label F 'Segment', count(B) 'Starts', "
        "sum(if(B='magnet_delivered',1,0)) 'Magnet', "
        "sum(if(B='handoff',1,0)) 'Handoff'\", 0)"
    )


def _verify_cli() -> int:
    """`python -m src.sheets` — connect, (re)create the header row, print status.

    Run this after configuring .env, or to repair the header row after clearing
    the sheet without restarting the bot.
    """
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )
    if not settings.analytics_enabled:
        print(
            "analytics not configured — set GOOGLE_SERVICE_ACCOUNT_JSON and "
            "ANALYTICS_SPREADSHEET_ID in .env"
        )
        return 1
    try:
        _open_worksheet()
    except Exception as error:  # noqa: BLE001
        print(f"FAILED — {_explain(error)}")
        return 1
    print(
        f"OK — worksheet '{settings.analytics_worksheet}' ready with header row.\n\n"
        "For a summary tab: add a sheet and paste this into A1 "
        "(swap ',' for ';' if your Sheets locale needs it):\n\n"
        f"  {_summary_formula()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_verify_cli())
