"""Entry point: build the Bot + Dispatcher, wire routers, start long polling."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings
from handlers import faq, fallback, handoff, menu, start


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(faq.router)
    dp.include_router(handoff.router)
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
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped")
