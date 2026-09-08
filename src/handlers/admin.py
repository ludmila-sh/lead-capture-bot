"""Admin-only commands. `/reload` re-reads the text overrides from the sheet."""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src import text_overrides
from src.config import settings

router = Router(name="admin")
logger = logging.getLogger(__name__)


@router.message(Command("reload"))
async def reload_texts(message: Message) -> None:
    user = message.from_user
    if user is None:
        return
    if user.id not in settings.admin_ids:
        await message.answer(
            f"⛔ /reload только для админа. Твой Telegram id: <code>{user.id}</code>. "
            "Добавь его в ADMIN_IDS (или EXPERT_CHAT_ID) в .env и перезапусти бота."
        )
        return
    logger.info("/reload by admin user_id=%s", user.id)
    summary = await text_overrides.reload()
    await message.answer(f"🔁 {summary}")
