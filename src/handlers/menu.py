"""Main menu navigation: root menu and the Практика (lead magnet) screen."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from src.content import texts
from src.events import log_event
from src.handlers.common import show
from src.keyboards import main_menu, practice_menu

router = Router(name="menu")
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "menu:root")
async def open_root(callback: CallbackQuery) -> None:
    log_event("tap", callback.from_user, target="menu")
    await show(callback, texts.MENU_PROMPT, main_menu())


@router.callback_query(F.data == "menu:practice")
async def open_practice(callback: CallbackQuery) -> None:
    # No segment context on a menu tap -> deliver the default lead magnet.
    log_event("tap", callback.from_user, target="practice")
    magnet = texts.lead_magnet(texts.DEFAULT_SEGMENT)
    await show(callback, magnet.text.format(link=magnet.link), practice_menu())
    log_event("magnet_delivered", callback.from_user, segment=texts.DEFAULT_SEGMENT)
    if isinstance(callback.message, Message):
        await callback.message.answer(magnet.question)
