from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

from src.content import texts
from src.handlers import faq, fallback, menu
from tests.conftest import read_events


def _callback(data: str, user_id: int = 111):
    cb = AsyncMock()
    cb.data = data
    cb.from_user = SimpleNamespace(id=user_id, username="u", full_name="U")
    cb.message = None  # not an aiogram Message -> show() just answers the callback
    return cb


async def test_open_practice_logs_tap_and_magnet(interaction_log):
    await menu.open_practice(_callback("menu:practice"))
    events = [e["event"] for e in read_events(interaction_log)]
    assert events == ["tap", "magnet_delivered"]
    assert read_events(interaction_log)[1]["segment"] == texts.DEFAULT_SEGMENT


async def test_faq_answer_valid_index_logs_view(interaction_log):
    await faq.open_faq_answer(_callback("faq:0"))
    recs = read_events(interaction_log)
    assert recs[0]["event"] == "faq_view"
    assert recs[0]["question"] == texts.FAQ[0][0]


async def test_faq_answer_bad_index_does_not_crash(interaction_log):
    await faq.open_faq_answer(_callback("faq:999"))
    await faq.open_faq_answer(_callback("faq:abc"))
    # no faq_view logged, no exception
    assert [e["event"] for e in read_events(interaction_log)] == []


async def test_fallback_message_logs_and_answers(interaction_log):
    msg = AsyncMock()
    msg.from_user = SimpleNamespace(id=5, username=None, full_name="X")
    msg.content_type = "sticker"
    await fallback.unknown_message(msg)

    msg.answer.assert_awaited_once()
    rec = read_events(interaction_log)[0]
    assert rec["event"] == "fallback"
    assert rec["content_type"] == "sticker"
