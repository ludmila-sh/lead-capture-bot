"""/start — greeting + main menu."""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from src.content import texts
from src.keyboards import main_menu

router = Router(name="start")
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else "unknown"
    logger.info("start: user_id=%s", user_id)
    await message.answer(texts.GREETING, reply_markup=main_menu())
