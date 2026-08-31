"""Main menu navigation: root menu and the Практика (lead magnet) screen."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from content import texts
from handlers.common import show
from keyboards import main_menu, practice_menu

router = Router(name="menu")
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "menu:root")
async def open_root(callback: CallbackQuery) -> None:
    logger.info("menu:root by user_id=%s", callback.from_user.id)
    await show(callback, texts.MENU_PROMPT, main_menu())


@router.callback_query(F.data == "menu:practice")
async def open_practice(callback: CallbackQuery) -> None:
    logger.info("menu:practice by user_id=%s", callback.from_user.id)
    text = texts.PRACTICE.format(link=texts.PRACTICE_LINK)
    await show(callback, text, practice_menu())
