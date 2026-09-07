"""Channel subscription tracking.

Requires the bot to be an administrator in the channel — only then does
Telegram deliver `chat_member` updates for other users. Logs `subscribed` /
`unsubscribed` events (mirrored to Google Sheets), attributing each to the
user's entry segment when known.

`my_chat_member` is logged too, so you can see in the console when the bot is
added to / removed from the channel.
"""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import (
    JOIN_TRANSITION,
    LEAVE_TRANSITION,
    ChatMemberUpdatedFilter,
)
from aiogram.types import Chat, ChatMemberUpdated

from src import state
from src.config import settings
from src.events import log_event

router = Router(name="subscription")
logger = logging.getLogger(__name__)


def _is_target_channel(chat: Chat) -> bool:
    if settings.channel_id:
        return str(chat.id) == settings.channel_id
    if settings.channel_username:
        return chat.username == settings.channel_username
    # Nothing to match against — trust that the bot is admin only in the channel.
    return True


def _describe(chat: Chat) -> str:
    return f"{chat.username or chat.title!r} (id={chat.id})"


@router.chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def on_join(event: ChatMemberUpdated) -> None:
    if not _is_target_channel(event.chat):
        logger.info("join in non-target chat %s — ignored", _describe(event.chat))
        return
    user = event.new_chat_member.user
    segment = state.segment_of(user.id)
    logger.info("subscribed: user_id=%s segment=%s", user.id, segment or "none")
    log_event("subscribed", user, segment=segment or "none")


@router.chat_member(ChatMemberUpdatedFilter(LEAVE_TRANSITION))
async def on_leave(event: ChatMemberUpdated) -> None:
    if not _is_target_channel(event.chat):
        logger.info("leave in non-target chat %s — ignored", _describe(event.chat))
        return
    user = event.new_chat_member.user
    segment = state.segment_of(user.id)
    logger.info("unsubscribed: user_id=%s segment=%s", user.id, segment or "none")
    log_event("unsubscribed", user, segment=segment or "none")


@router.chat_member()
async def on_other_chat_member(event: ChatMemberUpdated) -> None:
    # Any chat_member update that was not a clean join/leave. Logged so that a
    # missing "subscribed" can be told apart from "update never arrived".
    logger.info(
        "chat_member in %s: %s -> %s (no subscribed/unsubscribed logged)",
        _describe(event.chat),
        event.old_chat_member.status,
        event.new_chat_member.status,
    )


@router.my_chat_member()
async def on_bot_status(event: ChatMemberUpdated) -> None:
    logger.info(
        "bot membership in %s: %s -> %s",
        _describe(event.chat),
        event.old_chat_member.status,
        event.new_chat_member.status,
    )
