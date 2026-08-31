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

from src.content import texts
from src.keyboards import main_menu, practice_menu

router = Router(name="start")
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject) -> None:
    user_id = message.from_user.id if message.from_user else "unknown"
    raw = command.args  # text after "/start ", or None
    segment = texts.find_segment(raw)

    if segment is None:
        logger.info("start: user_id=%s segment=none raw=%r", user_id, raw)
        await message.answer(texts.GREETING, reply_markup=main_menu())
        return

    magnet = texts.LEAD_MAGNETS[segment]
    # segment == source tag; full logging / storage lands in Phase 3.
    logger.info("start: user_id=%s segment=%s (%s)", user_id, segment, magnet.label)
    body = f"{texts.GREETING_LEAD}\n\n{magnet.text.format(link=magnet.link)}"
    await message.answer(body, reply_markup=practice_menu())
