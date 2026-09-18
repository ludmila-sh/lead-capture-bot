from __future__ import annotations

import dataclasses
from types import SimpleNamespace
from unittest.mock import AsyncMock

from src.config import settings
from src.handlers import admin


def _message(user_id):
    return SimpleNamespace(
        from_user=SimpleNamespace(id=user_id) if user_id is not None else None,
        answer=AsyncMock(),
    )


async def test_health_replies_to_admin(monkeypatch):
    monkeypatch.setattr(
        admin, "settings", dataclasses.replace(settings, admin_ids=frozenset({777}))
    )
    message = _message(777)

    await admin.cmd_health(message)

    message.answer.assert_awaited_once()
    body = message.answer.call_args.args[0]
    assert "Аптайм" in body
    assert "Google Sheets" in body


async def test_health_ignores_non_admin(monkeypatch):
    monkeypatch.setattr(
        admin, "settings", dataclasses.replace(settings, admin_ids=frozenset({777}))
    )
    message = _message(999)

    await admin.cmd_health(message)

    message.answer.assert_not_awaited()


async def test_health_ignores_missing_user(monkeypatch):
    monkeypatch.setattr(
        admin, "settings", dataclasses.replace(settings, admin_ids=frozenset({777}))
    )
    message = _message(None)

    await admin.cmd_health(message)

    message.answer.assert_not_awaited()
