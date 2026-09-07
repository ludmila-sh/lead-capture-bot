"""Interaction logging.

Every meaningful funnel action is appended as one JSON line to
`settings.interaction_log_path` (and echoed to stdout) — this is the durable,
offline-safe record and the source for `python -m src.stats`.

A subset of events (funnel milestones) is also forwarded to the Google Sheets
sink for the client-facing report. The sink is best-effort and never blocks or
raises into the handler; JSONL above is always written first.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from aiogram.types import User

from src import sheets
from src.config import settings

logger = logging.getLogger("events")

_LOG_PATH = Path(settings.interaction_log_path)

# Events mirrored to Google Sheets (ROADMAP Phase 4).
_SHEET_EVENTS = {"start", "magnet_delivered", "handoff", "subscribed", "unsubscribed"}


def log_event(event: str, user: User | None, **fields: object) -> None:
    """Record one interaction. Never raises — logging must not lose a lead."""
    record: dict[str, object] = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "event": event,
        "user_id": user.id if user else None,
        "username": user.username if user else None,
        "name": user.full_name if user else None,
    }
    record.update(fields)

    logger.info("%s", record)
    try:
        _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as error:
        logger.warning("could not write interaction log: %s", error)

    if event in _SHEET_EVENTS:
        try:
            sheets.enqueue(
                event,
                user_id=record["user_id"],
                username=record["username"],
                name=record["name"],
                segment=fields.get("segment", ""),
                raw_param=fields.get("raw", ""),
                reason=fields.get("reason", ""),
            )
        except Exception as error:  # noqa: BLE001 - analytics must not break handlers
            logger.warning("sheets enqueue failed: %s", error)
