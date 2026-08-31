"""Interaction logging.

Every meaningful funnel action is appended as one JSON line to
`settings.interaction_log_path` (and echoed to stdout). File first; a
spreadsheet / DB sync comes later (ROADMAP Phase 5).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from aiogram.types import User

from src.config import settings

logger = logging.getLogger("events")

_LOG_PATH = Path(settings.interaction_log_path)


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
