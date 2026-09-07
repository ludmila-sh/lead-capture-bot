from __future__ import annotations

import dataclasses
from types import SimpleNamespace

from aiogram import Bot
from aiogram.types import Update

from src.config import settings
from src.handlers import subscription
from tests.conftest import read_events


def _chat(username="test_channel", chat_id=-1001):
    return SimpleNamespace(id=chat_id, username=username, title="Test Channel")


def test_is_target_channel_by_username():
    assert subscription._is_target_channel(_chat("test_channel")) is True
    assert subscription._is_target_channel(_chat("someone_else")) is False


def test_is_target_channel_by_id(monkeypatch):
    monkeypatch.setattr(
        subscription,
        "settings",
        dataclasses.replace(settings, channel_id="-100999", channel_url="https://x"),
    )
    assert subscription._is_target_channel(_chat("x", -100999)) is True
    assert subscription._is_target_channel(_chat("x", -100111)) is False


# --- integration through the dispatcher -----------------------------------


def _member_update(update_id: int, old: str, new: str, username="test_channel"):
    def member(status):
        return {
            "status": status,
            "user": {"id": 777, "is_bot": False, "first_name": "Joiner"},
        }

    return Update.model_validate(
        {
            "update_id": update_id,
            "chat_member": {
                "chat": {
                    "id": -1001,
                    "type": "channel",
                    "title": "Test Channel",
                    "username": username,
                },
                "from": {"id": 777, "is_bot": False, "first_name": "Joiner"},
                "date": 1_700_000_000,
                "old_chat_member": member(old),
                "new_chat_member": member(new),
            },
        }
    )


# aiogram routers are module-level singletons and can be attached to only one
# Dispatcher, so build it once for the whole module. The handlers under test do
# not make bot API calls, so the Bot's session is never opened.
from src.bot import build_dispatcher  # noqa: E402

_DP = build_dispatcher()
_BOT = Bot(token=settings.bot_token)


async def test_join_then_leave_logged(interaction_log):
    await _DP.feed_update(_BOT, _member_update(1, "left", "member"))
    await _DP.feed_update(_BOT, _member_update(2, "member", "left"))

    events = [(e["event"], e["user_id"]) for e in read_events(interaction_log)]
    assert events == [("subscribed", 777), ("unsubscribed", 777)]


async def test_join_in_other_channel_ignored(interaction_log):
    await _DP.feed_update(
        _BOT, _member_update(1, "left", "member", username="not_ours")
    )
    assert read_events(interaction_log) == []


def test_allowed_updates_include_chat_member():
    allowed = _DP.resolve_used_update_types()
    assert "chat_member" in allowed
    assert "my_chat_member" in allowed
