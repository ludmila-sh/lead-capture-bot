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


async def test_deep_link_delivers_segment_magnet(interaction_log):
    msg = _message()
    await cmd_start(msg, CommandObject(command="start", args="spina"))

    body = msg.answer.call_args.args[0]
    assert texts.GREETING_LEAD in body
    assert texts.LEAD_MAGNETS["spina"].link in body

    events = [e["event"] for e in read_events(interaction_log)]
    assert events == ["start", "magnet_delivered"]
    assert read_events(interaction_log)[0]["segment"] == "spina"
    assert state.segment_of(111) == "spina"


async def test_plain_start_shows_menu_no_magnet(interaction_log):
    msg = _message(222)
    await cmd_start(msg, CommandObject(command="start", args=None))

    assert msg.answer.call_args.args[0] == texts.GREETING
    events = [e["event"] for e in read_events(interaction_log)]
    assert events == ["start"]
    assert read_events(interaction_log)[0]["segment"] == "none"


async def test_unknown_param_is_safe_fallback(interaction_log):
    msg = _message(333)
    await cmd_start(msg, CommandObject(command="start", args="totally-unknown"))

    assert msg.answer.call_args.args[0] == texts.GREETING
    rec = read_events(interaction_log)[0]
    assert rec["event"] == "start"
    assert rec["segment"] == "none"
    assert rec["raw"] == "totally-unknown"
