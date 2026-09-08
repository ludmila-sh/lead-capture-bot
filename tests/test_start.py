from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

from aiogram.filters import CommandObject

from src import state
from src.content import texts
from src.handlers.start import cmd_start
from tests.conftest import read_events


def _message(user_id: int = 111):
    msg = AsyncMock()
    msg.from_user = SimpleNamespace(id=user_id, username="u", full_name="U")
    return msg


def _sent(msg):
    """(text_or_caption, reply_markup) from whichever send method was used."""
    if msg.answer_photo.await_count:
        call = msg.answer_photo.call_args
        return call.kwargs["caption"], call.kwargs["reply_markup"]
    call = msg.answer.call_args
    return call.args[0], call.kwargs["reply_markup"]


def _urls(markup) -> list[str]:
    return [b.url for row in markup.inline_keyboard for b in row if b.url]


async def test_deep_link_delivers_segment_magnet_in_one_message(interaction_log):
    msg = _message()
    await cmd_start(msg, CommandObject(command="start", args="spina"))

    magnet = texts.LEAD_MAGNETS["spina"]
    # exactly one message, no photo, no separate follow-up question
    assert msg.answer.await_count == 1
    assert msg.answer_photo.await_count == 0
    assert msg.answer_video.await_count == 0

    body = msg.answer.call_args.args[0]
    assert body.startswith(magnet.text)
    assert body.endswith(magnet.link)  # link appended -> Telegram shows the preview

    events = [e["event"] for e in read_events(interaction_log)]
    assert events == ["start", "magnet_delivered"]
    assert read_events(interaction_log)[0]["segment"] == "spina"
    assert state.segment_of(111) == "spina"


async def test_deep_link_with_video_sends_video(interaction_log, monkeypatch):
    import dataclasses

    from src.handlers import start as start_mod

    vid_magnet = dataclasses.replace(
        texts.LEAD_MAGNETS["spina"], video="BAAC-file-id-123"
    )
    monkeypatch.setitem(texts.LEAD_MAGNETS, "spina", vid_magnet)

    msg = _message()
    await start_mod.cmd_start(msg, CommandObject(command="start", args="spina"))

    msg.answer_video.assert_awaited_once()
    assert msg.answer_video.call_args.args[0] == "BAAC-file-id-123"
    assert msg.answer_video.call_args.kwargs["caption"] == vid_magnet.text
    assert msg.answer.await_count == 0


async def test_plain_start_shows_greeting_and_menu(interaction_log):
    msg = _message(222)
    await cmd_start(msg, CommandObject(command="start", args=None))

    body, _ = _sent(msg)
    assert body == texts.GREETING
    events = [e["event"] for e in read_events(interaction_log)]
    assert events == ["start"]
    assert read_events(interaction_log)[0]["segment"] == "none"


async def test_unknown_param_is_safe_fallback(interaction_log):
    msg = _message(333)
    await cmd_start(msg, CommandObject(command="start", args="totally-unknown"))

    body, _ = _sent(msg)
    assert body == texts.GREETING
    rec = read_events(interaction_log)[0]
    assert rec["event"] == "start"
    assert rec["segment"] == "none"
    assert rec["raw"] == "totally-unknown"
