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


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        bot_token=_require("BOT_TOKEN"),
        expert_handoff_username=_require("EXPERT_HANDOFF_USERNAME").lstrip("@"),
        channel_url=_require("CHANNEL_URL"),
    )


# Loaded once at import time; handlers and keyboards import this singleton.
settings = load_settings()
