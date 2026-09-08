"""/start — entry point of the funnel.

  * plain /start      -> greeting (with Artyom's photo when bundled) + main menu
  * /start <segment>  -> the segment's practice, one message:
        - `video` set  -> the video sent straight into the chat
        - else         -> text + link (Telegram shows the video's preview card)
        plus [📣 Подписаться на канал] / [🏠 В меню]
Unknown parameter -> safe fallback: treated as plain /start, raw value logged.
"""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import FSInputFile, Message

from src import state
from src.content import texts
from src.content.texts import LeadMagnet
from src.events import log_event
from src.keyboards import magnet_menu, main_menu

router = Router(name="start")
logger = logging.getLogger(__name__)


async def _send_greeting(message: Message) -> None:
    """Plain greeting: photo + caption when the portrait is bundled, else text."""
    if texts.GREETING_PHOTO is not None:
        try:
            await message.answer_photo(
                FSInputFile(texts.GREETING_PHOTO),
                caption=texts.GREETING,
                reply_markup=main_menu(),
            )
            return
        except TelegramAPIError as error:
            logger.warning("greeting photo failed, sending text: %s", error)
    await message.answer(texts.GREETING, reply_markup=main_menu())


async def _deliver_magnet(message: Message, magnet: LeadMagnet) -> None:
    """One message with the practice: video file, or text + link preview."""
    if magnet.video:
        try:
            await message.answer_video(
                magnet.video, caption=magnet.text, reply_markup=magnet_menu()
            )
            return
        except TelegramAPIError as error:
            logger.warning("video send failed, falling back to link: %s", error)
    body = f"{magnet.text}\n\n{magnet.link}" if magnet.link else magnet.text
    await message.answer(body, reply_markup=magnet_menu())


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject) -> None:
    user = message.from_user
    raw = command.args  # text after "/start ", or None
    segment = texts.find_segment(raw)

    if segment is None:
        log_event("start", user, segment="none", raw=raw)
        await _send_greeting(message)
        return

    if user is not None:
        state.remember_segment(user.id, segment)
    magnet = texts.LEAD_MAGNETS[segment]
    log_event("start", user, segment=segment)
    await _deliver_magnet(message, magnet)
    log_event("magnet_delivered", user, segment=segment)
