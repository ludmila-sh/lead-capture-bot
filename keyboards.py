"""Inline keyboards. Callback data scheme:

  menu:root      -> main menu
  menu:practice  -> lead magnet screen
  menu:faq       -> FAQ question list
  menu:expert    -> handoff screen
  faq:<index>    -> a single FAQ answer
"""

from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import settings
from content import texts


def main_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=texts.BTN_PRACTICE, callback_data="menu:practice")
    kb.button(text=texts.BTN_FAQ, callback_data="menu:faq")
    kb.button(text=texts.BTN_EXPERT, callback_data="menu:expert")
    kb.adjust(1)
    return kb.as_markup()


def practice_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=texts.BTN_SUBSCRIBE, url=settings.channel_url)
    kb.button(text=texts.BTN_BACK_TO_MENU, callback_data="menu:root")
    kb.adjust(1)
    return kb.as_markup()


def faq_list_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for index, (question, _answer) in enumerate(texts.FAQ):
        kb.button(text=question, callback_data=f"faq:{index}")
    kb.button(text=texts.BTN_BACK_TO_MENU, callback_data="menu:root")
    kb.adjust(1)
    return kb.as_markup()


def faq_answer_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=texts.BTN_BACK_TO_FAQ, callback_data="menu:faq")
    kb.button(text=texts.BTN_BACK_TO_MENU, callback_data="menu:root")
    kb.adjust(1)
    return kb.as_markup()


def expert_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=texts.BTN_WRITE_EXPERT, url=settings.expert_url)
    kb.button(text=texts.BTN_BACK_TO_MENU, callback_data="menu:root")
    kb.adjust(1)
    return kb.as_markup()
