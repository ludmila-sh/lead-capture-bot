"""Entry point: build the Bot + Dispatcher, wire routers, start long polling."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.config import settings
from src.handlers import faq, fallback, handoff, menu, start, subscription


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
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
    logging.info("Bot @%s started (long polling)", me.username)
    # resolve_used_update_types() adds chat_member / my_chat_member because the
    # subscription router registers handlers for them (not on by default).
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped")
