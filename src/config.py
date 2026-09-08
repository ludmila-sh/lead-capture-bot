"""Load deployment configuration from the environment (.env via python-dotenv).

Values here differ per client deployment. Client-facing *text* lives in
content/texts.py; this module only holds secrets and per-deployment URLs.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

from dotenv import load_dotenv

_PLACEHOLDERS = {"", "your-token-here", "expert_username", "https://t.me/your_channel"}


@dataclass(frozen=True)
class Settings:
    bot_token: str
    expert_handoff_username: str
    channel_url: str
    # Numeric id of the channel (e.g. "-1001234567890"), used to recognise
    # chat_member updates for subscription tracking. Optional: for a public
    # channel the @username is parsed from channel_url instead.
    channel_id: str
    # Numeric chat id of the expert, so the bot can *send* them lead
    # notifications (a bot cannot message a user by @username). Optional:
    # if unset, handoff still works — the user just gets the link.
    expert_chat_id: int | None
    # Where interaction events are appended as JSON lines.
    interaction_log_path: str
    # Google Sheets analytics sink. All optional; the sink is active only when
    # both the service-account key path and the spreadsheet id are set.
    google_service_account_json: str
    analytics_spreadsheet_id: str
    analytics_worksheet: str
    # Live text overrides: a worksheet (key | value) in the analytics spreadsheet
    # the client edits; the bot re-reads it on a timer and on /reload. Needs the
    # same Google Sheets access as analytics.
    texts_worksheet: str
    texts_reload_seconds: int  # 0 = never auto-reload
    # Telegram user ids allowed to run /reload. Defaults to {expert_chat_id}.
    admin_ids: frozenset[int]

    @property
    def expert_url(self) -> str:
        return f"https://t.me/{self.expert_handoff_username}"

    @property
    def channel_username(self) -> str | None:
        """@username parsed from channel_url, or None for a private invite link."""
        match = re.search(r"t\.me/([A-Za-z0-9_]{4,})/?$", self.channel_url)
        return match.group(1) if match else None

    @property
    def analytics_enabled(self) -> bool:
        return bool(self.google_service_account_json and self.analytics_spreadsheet_id)


def _require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if value in _PLACEHOLDERS:
        raise RuntimeError(
            f"Environment variable {name} is missing or still set to a placeholder. "
            f"Copy env.example to .env and fill it in."
        )
    return value


def _optional_int(name: str) -> int | None:
    value = os.environ.get(name, "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        raise RuntimeError(
            f"Environment variable {name} must be an integer, got {value!r}"
        )


def _parse_ids(raw: str, fallback: int | None) -> frozenset[int]:
    ids = {
        int(tok) for tok in raw.replace(",", " ").split() if tok.lstrip("-").isdigit()
    }
    if not ids and fallback is not None:
        ids.add(fallback)
    return frozenset(ids)


def load_settings() -> Settings:
    load_dotenv()
    expert_chat_id = _optional_int("EXPERT_CHAT_ID")
    reload_seconds = _optional_int("TEXTS_RELOAD_SECONDS")
    return Settings(
        bot_token=_require("BOT_TOKEN"),
        expert_handoff_username=_require("EXPERT_HANDOFF_USERNAME").lstrip("@"),
        channel_url=_require("CHANNEL_URL"),
        channel_id=os.environ.get("CHANNEL_ID", "").strip(),
        expert_chat_id=expert_chat_id,
        interaction_log_path=os.environ.get("INTERACTION_LOG_PATH", "").strip()
        or "data/interactions.jsonl",
        google_service_account_json=os.environ.get(
            "GOOGLE_SERVICE_ACCOUNT_JSON", ""
        ).strip(),
        analytics_spreadsheet_id=os.environ.get("ANALYTICS_SPREADSHEET_ID", "").strip(),
        analytics_worksheet=os.environ.get("ANALYTICS_WORKSHEET", "").strip()
        or "events",
        texts_worksheet=os.environ.get("TEXTS_WORKSHEET", "").strip() or "Тексты бота",
        texts_reload_seconds=180 if reload_seconds is None else reload_seconds,
        admin_ids=_parse_ids(os.environ.get("ADMIN_IDS", ""), expert_chat_id),
    )


# Loaded once at import time; handlers and keyboards import this singleton.
settings = load_settings()
