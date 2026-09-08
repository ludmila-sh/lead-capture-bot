from __future__ import annotations

import dataclasses

import pytest

from src.config import Settings, _optional_int, settings


def _make(**overrides) -> Settings:
    base = dict(
        bot_token="t",
        expert_handoff_username="exp",
        channel_url="https://t.me/some_channel",
        channel_id="",
        expert_chat_id=None,
        interaction_log_path="x.jsonl",
        google_service_account_json="",
        analytics_spreadsheet_id="",
        analytics_worksheet="events",
        texts_worksheet="Тексты бота",
        texts_reload_seconds=0,
        admin_ids=frozenset(),
    )
    base.update(overrides)
    return Settings(**base)


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://t.me/my_channel", "my_channel"),
        ("https://t.me/my_channel/", "my_channel"),
        ("http://t.me/AbC_123", "AbC_123"),
        ("https://t.me/+AbCdEfInvite", None),  # private invite link
        ("https://example.com/x", None),
    ],
)
def test_channel_username_parsing(url, expected):
    assert _make(channel_url=url).channel_username == expected


def test_expert_url():
    assert _make(expert_handoff_username="coach").expert_url == "https://t.me/coach"


def test_analytics_enabled_requires_both():
    assert _make().analytics_enabled is False
    assert _make(google_service_account_json="k.json").analytics_enabled is False
    assert _make(analytics_spreadsheet_id="ID").analytics_enabled is False
    assert (
        _make(
            google_service_account_json="k.json", analytics_spreadsheet_id="ID"
        ).analytics_enabled
        is True
    )


def test_optional_int(monkeypatch):
    monkeypatch.delenv("SOME_INT", raising=False)
    assert _optional_int("SOME_INT") is None
    monkeypatch.setenv("SOME_INT", "  ")
    assert _optional_int("SOME_INT") is None
    monkeypatch.setenv("SOME_INT", "-100123")
    assert _optional_int("SOME_INT") == -100123
    monkeypatch.setenv("SOME_INT", "abc")
    with pytest.raises(RuntimeError):
        _optional_int("SOME_INT")


def test_settings_singleton_is_frozen():
    with pytest.raises(dataclasses.FrozenInstanceError):
        settings.bot_token = "nope"  # type: ignore[misc]
