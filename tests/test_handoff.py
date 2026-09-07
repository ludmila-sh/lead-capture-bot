from __future__ import annotations

import dataclasses
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.config import settings
from src.handlers import handoff
from tests.conftest import read_events


@pytest.mark.parametrize(
    "text, expected",
    [
        ("у меня болит спина", True),
        ("после родов тяжело даётся наклон, болит поясница", True),
        ("грыжа l5-s1, можно заниматься?", True),
        ("сколько стоит абонемент?", False),
        ("во сколько занятие в четверг?", False),
        ("/start spina", False),
        ("", False),
    ],
)
def test_is_health_question(text, expected):
    msg = SimpleNamespace(text=text)
    assert handoff.is_health_question(msg) is expected


def _carrier(text=None, user_id=555):
    return SimpleNamespace(
        from_user=SimpleNamespace(id=user_id, username="lead", full_name="Лид Лидов"),
        bot=AsyncMock(),
        text=text,
    )


async def test_notify_expert_without_chat_id_logs_but_does_not_send(interaction_log):
    assert settings.expert_chat_id is None  # conftest
    carrier = _carrier()
    await handoff.notify_expert(carrier, reason="нажал «Написать эксперту»")

    carrier.bot.send_message.assert_not_awaited()
    rec = read_events(interaction_log)[0]
    assert rec["event"] == "handoff"
    assert rec["reason"] == "нажал «Написать эксперту»"
    assert rec["notified"] is False


async def test_notify_expert_with_chat_id_sends_card(monkeypatch, interaction_log):
    monkeypatch.setattr(
        handoff, "settings", dataclasses.replace(settings, expert_chat_id=42)
    )
    carrier = _carrier(text="болит спина уже месяц")
    await handoff.notify_expert(carrier, reason="вопрос о здоровье")

    chat_id, body = carrier.bot.send_message.call_args.args
    assert chat_id == 42
    assert "Лид Лидов" in body
    assert "@lead" in body
    assert "вопрос о здоровье" in body
    assert "болит спина уже месяц" in body  # incoming text appended
    assert read_events(interaction_log)[0]["notified"] is True


async def test_notify_expert_swallows_send_errors(monkeypatch, interaction_log):
    from aiogram.exceptions import TelegramForbiddenError

    monkeypatch.setattr(
        handoff, "settings", dataclasses.replace(settings, expert_chat_id=42)
    )
    carrier = _carrier()
    carrier.bot.send_message = AsyncMock(
        side_effect=TelegramForbiddenError(method=None, message="blocked")
    )
    # Must not raise.
    await handoff.notify_expert(carrier, reason="x")
    assert read_events(interaction_log)[0]["event"] == "handoff"
