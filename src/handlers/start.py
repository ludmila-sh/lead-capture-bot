"""/start — entry point of the funnel.

Plain /start (no parameter) -> greeting + main menu.
Deep link /start <segment> (t.me/<bot>?start=spina) -> greet, deliver that
segment's lead magnet immediately, then offer the channel + menu.
Unknown parameter -> safe fallback: treated as plain /start, raw value logged.
"""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message

from src import state
from src.content import texts
from src.events import log_event
from src.keyboards import main_menu, practice_menu

router = Router(name="start")
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject) -> None:
    user = message.from_user
    raw = command.args  # text after "/start ", or None
    segment = texts.find_segment(raw)

    if segment is None:
        log_event("start", user, segment="none", raw=raw)
        await message.answer(texts.GREETING, reply_markup=main_menu())
        return

    if user is not None:
        state.remember_segment(user.id, segment)
    magnet = texts.LEAD_MAGNETS[segment]
    log_event("start", user, segment=segment)
    body = f"{texts.GREETING_LEAD}\n\n{magnet.text.format(link=magnet.link)}"
    await message.answer(body, reply_markup=practice_menu())
    log_event("magnet_delivered", user, segment=segment)
