"""Написать эксперту — hand the lead to the human expert.

Phase 1: show a message with a link to the expert's chat. Phase 3 adds
notifying the expert directly and logging.
"""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from src.content import texts
from src.handlers.common import show
from src.keyboards import expert_menu

router = Router(name="handoff")
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "menu:expert")
async def open_expert(callback: CallbackQuery) -> None:
    logger.info("handoff requested by user_id=%s", callback.from_user.id)
    await show(callback, texts.EXPERT, expert_menu())
