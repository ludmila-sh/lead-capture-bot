"""Load deployment configuration from the environment (.env via python-dotenv).

Values here differ per client deployment. Client-facing *text* lives in
content/texts.py; this module only holds secrets and per-deployment URLs.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

_PLACEHOLDERS = {"", "your-token-here", "expert_username", "https://t.me/your_channel"}


@dataclass(frozen=True)
class Settings:
    bot_token: str
    expert_handoff_username: str
    channel_url: str
    # Numeric chat id of the expert, so the bot can *send* them lead
    # notifications (a bot cannot message a user by @username). Optional:
    # if unset, handoff still works — the user just gets the link.
    expert_chat_id: int | None
    # Where interaction events are appended as JSON lines.
    interaction_log_path: str

    @property
    def expert_url(self) -> str:
        return f"https://t.me/{self.expert_handoff_username}"


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


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        bot_token=_require("BOT_TOKEN"),
        expert_handoff_username=_require("EXPERT_HANDOFF_USERNAME").lstrip("@"),
        channel_url=_require("CHANNEL_URL"),
        expert_chat_id=_optional_int("EXPERT_CHAT_ID"),
        interaction_log_path=os.environ.get("INTERACTION_LOG_PATH", "").strip()
        or "data/interactions.jsonl",
    )


# Loaded once at import time; handlers and keyboards import this singleton.
settings = load_settings()
