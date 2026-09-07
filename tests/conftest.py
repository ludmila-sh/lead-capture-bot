"""Test config. Environment is set here BEFORE any `src.*` import, because
`src.config` builds its settings singleton at import time.
"""

from __future__ import annotations

import os
import pathlib
import tempfile

# Deterministic, non-secret settings for the whole test session.
os.environ.setdefault("BOT_TOKEN", "123456789:AABBCCDDEEFFGGHHIIJJKKLLMMNNOOPPQQRR")
os.environ.setdefault("EXPERT_HANDOFF_USERNAME", "expert_acc")
os.environ.setdefault("CHANNEL_URL", "https://t.me/test_channel")
# Force these OFF regardless of any real .env: an empty value in os.environ wins
# over the .env file because python-dotenv does not override existing vars.
os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"] = ""
os.environ["ANALYTICS_SPREADSHEET_ID"] = ""
os.environ["EXPERT_CHAT_ID"] = ""
os.environ["CHANNEL_ID"] = ""

_LOG_PATH = pathlib.Path(tempfile.gettempdir()) / "lcb_test_interactions.jsonl"
os.environ["INTERACTION_LOG_PATH"] = str(_LOG_PATH)

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def clean_interaction_log():
    _LOG_PATH.unlink(missing_ok=True)
    yield
    _LOG_PATH.unlink(missing_ok=True)


@pytest.fixture
def interaction_log() -> pathlib.Path:
    return _LOG_PATH


def read_events(path: pathlib.Path) -> list[dict]:
    import json

    if not path.is_file():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]
