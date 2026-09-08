"""Live text overrides from a Google Sheet.

A `key | value` worksheet (default «Тексты бота») in the analytics spreadsheet
lets the client edit copy without touching code. The bot re-reads it:
  * once at startup,
  * every `TEXTS_RELOAD_SECONDS` (0 = off),
  * on `/reload` from an admin.

Invalid edits are rejected as a whole — the bot keeps the last good texts.
"""

from __future__ import annotations

import asyncio
import logging

from src.config import settings
from src.content import texts

logger = logging.getLogger("texts")


def _fetch() -> dict[str, str]:
    """Read the override worksheet (blocking).

    Any row whose first cell is a recognised override key is used, regardless of
    where the header / title rows sit — so the tab layout can change freely.
    """
    import gspread

    client = gspread.service_account(filename=settings.google_service_account_json)
    spreadsheet = client.open_by_key(settings.analytics_spreadsheet_id)
    worksheet = spreadsheet.worksheet(settings.texts_worksheet)
    result: dict[str, str] = {}
    for row in worksheet.get_all_values():
        if len(row) >= 2 and texts.is_override_key(row[0]) and row[1].strip():
            result[row[0].strip()] = row[1]
    return result


async def reload() -> str:
    """Fetch overrides and apply them. Returns a short human-readable summary."""
    if not settings.analytics_enabled:
        return "overrides off (no Google Sheets access configured)"
    try:
        overrides = await asyncio.to_thread(_fetch)
    except Exception as error:  # noqa: BLE001 - any gspread error, report and move on
        return f"could not read «{settings.texts_worksheet}»: {error}"
    if not overrides:
        return (
            f"«{settings.texts_worksheet}»: нет строк с известными ключами "
            "(напр. faq.1.a) и непустым значением — использую тексты из кода"
        )
    try:
        applied = await asyncio.to_thread(texts.apply_overrides, overrides)
    except RuntimeError as error:
        return f"НЕ применено (ошибка проверки): {error}"
    return "Тексты обновлены ✅"


async def poll_forever() -> None:
    """Background loop: reload on the configured interval. Never raises."""
    interval = settings.texts_reload_seconds
    while True:
        await asyncio.sleep(interval)
        try:
            logger.info("texts reload (poll): %s", await reload())
        except Exception as error:  # noqa: BLE001
            logger.warning("texts poll failed: %s", error)
