"""Shared helper for swapping the current screen without ever crashing."""

from __future__ import annotations

import logging

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

logger = logging.getLogger(__name__)


async def show(
    callback: CallbackQuery,
    text: str,
    markup: InlineKeyboardMarkup | None,
) -> None:
    """Edit the message behind `callback` to the new screen.

    Falls back to sending a fresh message if the edit fails (message too old,
    identical content, deleted, ...). Always answers the callback so the
    client stops showing a spinner. Never raises.
    """
    message = callback.message
    if isinstance(message, Message):
        try:
            await message.edit_text(text, reply_markup=markup)
            await callback.answer()
            return
        except TelegramBadRequest as error:
            logger.debug("edit_text failed (%s); sending a new message", error)
            try:
                await message.answer(text, reply_markup=markup)
            except TelegramBadRequest as send_error:
                logger.warning("could not send fallback message: %s", send_error)
    await callback.answer()
