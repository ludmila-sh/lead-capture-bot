from __future__ import annotations

import dataclasses
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.config import settings
from src.content import texts
from src.handlers import fallback, handoff
from tests.conftest import read_events


async def test_free_text_with_health_keyword_falls_back_without_notifying_expert(
    interaction_log,
):
    """Free text is never scanned for health keywords — it's a plain fallback."""
    message = SimpleNamespace(
        text="у меня болит спина",
        content_type="text",
        from_user=SimpleNamespace(id=555, username="lead", full_name="Лид Лидов"),
        answer=AsyncMock(),
    )
    await fallback.unknown_message(message)

    message.answer.assert_awaited_once()
    assert message.answer.call_args.args[0] == texts.FALLBACK
    rec = read_events(interaction_log)[0]
    assert rec["event"] == "fallback"
    assert not hasattr(handoff, "is_health_question")


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
