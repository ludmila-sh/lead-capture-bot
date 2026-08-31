"""Частые вопросы — question list and single-answer screens."""

from __future__ import annotations

import html
import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from src.content import texts
from src.handlers.common import show
from src.keyboards import faq_answer_menu, faq_list_menu

router = Router(name="faq")
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "menu:faq")
async def open_faq_list(callback: CallbackQuery) -> None:
    logger.info("menu:faq by user_id=%s", callback.from_user.id)
    await show(callback, texts.FAQ_INTRO, faq_list_menu())


@router.callback_query(F.data.startswith("faq:"))
async def open_faq_answer(callback: CallbackQuery) -> None:
    raw_index = (callback.data or "").split(":", 1)[1]
    try:
        question, answer = texts.FAQ[int(raw_index)]
    except (ValueError, IndexError):
        # Unknown / stale FAQ id — fall back to the question list.
        logger.warning("bad faq id %r from user_id=%s", raw_index, callback.from_user.id)
        await show(callback, texts.FAQ_INTRO, faq_list_menu())
        return

    logger.info("faq:%s by user_id=%s", raw_index, callback.from_user.id)
    body = f"<b>{html.escape(question)}</b>\n\n{html.escape(answer)}"
    await show(callback, body, faq_answer_menu())
