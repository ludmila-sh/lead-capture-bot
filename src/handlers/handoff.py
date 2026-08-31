"""Написать эксперту — hand the lead to the human expert.

Two triggers:
  * the "💬 Написать эксперту" button;
  * a free-text message that looks like a health question (bot never answers
    those — see CLAUDE.md).

Both notify the expert's chat (if EXPERT_CHAT_ID is set) with short context
and record a "handoff" interaction event.
"""

from __future__ import annotations

import html
import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery, Message

from src import state
from src.config import settings
from src.content import texts
from src.events import log_event
from src.handlers.common import show
from src.keyboards import expert_menu

router = Router(name="handoff")
logger = logging.getLogger(__name__)


def is_health_question(message: Message) -> bool:
    """True if a plain-text message mentions health/pain — a handoff trigger."""
    text = (message.text or "").strip().lower()
    if not text or text.startswith("/"):
        return False
    return any(keyword in text for keyword in texts.HEALTH_KEYWORDS)


async def notify_expert(message_or_cb: Message | CallbackQuery, reason: str) -> None:
    """Send the expert short context about a lead. Never raises."""
    user = message_or_cb.from_user
    bot = message_or_cb.bot
    segment_key = state.segment_of(user.id) if user else None
    segment_label = (
        texts.LEAD_MAGNETS[segment_key].label
        if segment_key in texts.LEAD_MAGNETS
        else "—"
    )
    contact = f"@{user.username}" if user and user.username else "нет username"

    log_event(
        "handoff",
        user,
        reason=reason,
        segment=segment_key or "none",
        notified=settings.expert_chat_id is not None,
    )

    if settings.expert_chat_id is None:
        logger.info("handoff (%s) but EXPERT_CHAT_ID unset — not notifying", reason)
        return

    body = texts.HANDOFF_TO_EXPERT.format(
        name=html.escape(user.full_name if user else "—"),
        contact=html.escape(contact),
        user_id=user.id if user else "—",
        segment=html.escape(segment_label),
        reason=html.escape(reason),
    )
    incoming = getattr(message_or_cb, "text", None)
    if incoming:
        body += f"\n\nСообщение:\n{html.escape(incoming)}"

    try:
        await bot.send_message(settings.expert_chat_id, body)
    except TelegramAPIError as error:
        logger.warning("could not notify expert: %s", error)


@router.callback_query(F.data == "menu:expert")
async def open_expert(callback: CallbackQuery) -> None:
    logger.info("handoff requested by user_id=%s", callback.from_user.id)
    await notify_expert(callback, reason="нажал «Написать эксперту»")
    await show(callback, texts.HANDOFF_ACK, expert_menu())


@router.message(is_health_question)
async def health_question(message: Message) -> None:
    logger.info("health question from user_id=%s", message.from_user.id)
    await notify_expert(message, reason="вопрос о здоровье")
    await message.answer(texts.HEALTH_REPLY, reply_markup=expert_menu())
