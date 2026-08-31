"""Catch-all. Included LAST so specific handlers win.

Any unrecognised message or callback re-shows the menu instead of failing —
losing a lead to an error is the worst possible outcome.
"""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.types import CallbackQuery, Message

from content import texts
from keyboards import main_menu

router = Router(name="fallback")
logger = logging.getLogger(__name__)


@router.message()
async def unknown_message(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else "unknown"
    logger.info("fallback message: user_id=%s content_type=%s", user_id, message.content_type)
    await message.answer(texts.FALLBACK, reply_markup=main_menu())


@router.callback_query()
async def unknown_callback(callback: CallbackQuery) -> None:
    logger.info("fallback callback: data=%r user_id=%s", callback.data, callback.from_user.id)
    if isinstance(callback.message, Message):
        await callback.message.answer(texts.FALLBACK, reply_markup=main_menu())
    await callback.answer()
