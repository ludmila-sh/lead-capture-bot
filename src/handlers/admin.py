"""Admin-only commands. All are silent for anyone not in ADMIN_IDS — no error
reply, so a random user can't even tell the command exists.

* /reload — re-reads the text overrides from the sheet.
* /health — manual "is it alive" check for the developer (uptime, today's
  event count, Google Sheets reachability). Not a monitoring endpoint, just a
  Telegram command.
* /status — weekly lead summary for Artyom (event counts, last 7 days), read
  straight from the local JSONL log. On demand only, no scheduler.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src import sheets, text_overrides
from src.config import settings

router = Router(name="admin")
logger = logging.getLogger(__name__)

_STARTED_AT = datetime.now(timezone.utc)


@router.message(Command("reload"))
async def reload_texts(message: Message) -> None:
    user = message.from_user
    if user is None or user.id not in settings.admin_ids:
        return  # silent for non-admins — don't confirm the command even exists
    logger.info("/reload by admin user_id=%s", user.id)
    summary = await text_overrides.reload()
    await message.answer(f"🔁 {summary}")


def _format_uptime(seconds: float) -> str:
    total = int(seconds)
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}ч {minutes}м"
    if minutes:
        return f"{minutes}м {secs}с"
    return f"{secs}с"


def _today_event_stats() -> str:
    """Count of interactions logged today (UTC), or the last event's time."""
    path = Path(settings.interaction_log_path)
    if not path.is_file():
        return "нет данных (лог пуст)"
    today = datetime.now(timezone.utc).date().isoformat()
    count_today = 0
    last_ts: str | None = None
    try:
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = record.get("ts")
                if not ts:
                    continue
                last_ts = ts
                if ts.startswith(today):
                    count_today += 1
    except OSError as error:
        return f"не удалось прочитать лог: {error}"
    if count_today:
        return f"{count_today} за сегодня"
    if last_ts:
        return f"0 за сегодня, последнее событие: {last_ts}"
    return "нет данных (лог пуст)"


def _sheets_status() -> str:
    if not settings.analytics_enabled:
        return "не настроено"
    ok, detail, checked_at = sheets.health()
    if ok is None:
        return "пока не проверялось"
    if ok:
        return f"ок (проверено {checked_at})"
    return f"недоступно — {detail} (проверено {checked_at})"


@router.message(Command("health"))
async def cmd_health(message: Message) -> None:
    user = message.from_user
    if user is None or user.id not in settings.admin_ids:
        return  # silent for non-admins — this is a dev diagnostic, not a funnel screen
    logger.info("/health requested by admin user_id=%s", user.id)
    uptime = _format_uptime((datetime.now(timezone.utc) - _STARTED_AT).total_seconds())
    await message.answer(
        "✅ Бот работает\n"
        f"Аптайм: {uptime}\n"
        f"События сегодня: {_today_event_stats()}\n"
        f"Google Sheets: {_sheets_status()}"
    )


# Events counted by /status, in display order. Same vocabulary as the
# "Воронка" block on the 📈 Дашборд tab (scripts/build_workspace.py) — keep
# labels in sync so the two never disagree on what a word means.
_WEEKLY_EVENTS = ("start", "magnet_delivered", "subscribed", "unsubscribed", "handoff")
_WEEKLY_LABELS = {
    "start": "Переходов в бот",
    "magnet_delivered": "Практик выдано",
    "subscribed": "Подписок",
    "unsubscribed": "Отписок",
    "handoff": "Обращений к Артёму",
}


def _weekly_summary(days: int = 7) -> str:
    """Counts of key events in the last `days` days, straight from the JSONL.

    Never raises: a missing file, a bad line, or a malformed timestamp is
    skipped rather than crashing the /status reply.
    """
    path = Path(settings.interaction_log_path)
    if not path.is_file():
        return "нет данных (лог пуст)"
    since = datetime.now(timezone.utc) - timedelta(days=days)
    counts = {event: 0 for event in _WEEKLY_EVENTS}
    try:
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    event = record.get("event")
                    ts = datetime.fromisoformat(record["ts"])
                except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                    continue
                if event in counts and ts >= since:
                    counts[event] += 1
    except OSError as error:
        return f"не удалось прочитать лог: {error}"
    return "\n".join(
        f"{_WEEKLY_LABELS[event]}: {counts[event]}" for event in _WEEKLY_EVENTS
    )


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    user = message.from_user
    if user is None or user.id not in settings.admin_ids:
        return  # silent for non-admins
    logger.info("/status requested by admin user_id=%s", user.id)
    await message.answer(f"📊 Сводка за 7 дней\n{_weekly_summary()}")
