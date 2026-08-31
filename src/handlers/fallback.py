"""Catch-all. Included LAST so specific handlers win.

Any unrecognised message or callback re-shows the menu instead of failing —
losing a lead to an error is the worst possible outcome.
"""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.types import CallbackQuery, Message

from src.content import texts
from src.events import log_event
from src.keyboards import main_menu

router = Router(name="fallback")
logger = logging.getLogger(__name__)


@router.message()
async def unknown_message(message: Message) -> None:
    log_event("fallback", message.from_user, content_type=message.content_type)
    await message.answer(texts.FALLBACK, reply_markup=main_menu())


@router.callback_query()
async def unknown_callback(callback: CallbackQuery) -> None:
    log_event("fallback", callback.from_user, data=callback.data)
    if isinstance(callback.message, Message):
        await callback.message.answer(texts.FALLBACK, reply_markup=main_menu())
    await callback.answer()
