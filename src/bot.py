"""Entry point: build the Bot + Dispatcher, wire routers, start long polling."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src import text_overrides
from src.config import settings
from src.handlers import admin, faq, fallback, handoff, menu, start, subscription


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(faq.router)
    dp.include_router(handoff.router)
    dp.include_router(subscription.router)
    dp.include_router(fallback.router)  # keep last: catch-all
    return dp


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = build_dispatcher()

    await bot.delete_webhook(drop_pending_updates=True)
    me = await bot.get_me()

    # Apply Google Sheet text overrides on boot, then keep polling them.
    logging.info(
        "text overrides: worksheet=%r, admins=%s, poll=%ss",
        settings.texts_worksheet,
        sorted(settings.admin_ids),
        settings.texts_reload_seconds,
    )
    logging.info("texts: %s", await text_overrides.reload())
    if settings.texts_reload_seconds > 0:
        asyncio.create_task(text_overrides.poll_forever())

    # resolve_used_update_types() adds chat_member / my_chat_member because the
    # subscription router registers handlers for them (not on by default).
    allowed = dp.resolve_used_update_types()
    logging.info(
        "Bot @%s started (long polling); allowed_updates=%s", me.username, allowed
    )
    await dp.start_polling(bot, allowed_updates=allowed)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped")
