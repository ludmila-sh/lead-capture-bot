from __future__ import annotations

import dataclasses
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

from src.config import settings
from src.handlers import admin


def _message(user_id):
    return SimpleNamespace(
        from_user=SimpleNamespace(id=user_id) if user_id is not None else None,
        answer=AsyncMock(),
    )


async def test_reload_runs_for_admin(monkeypatch):
    monkeypatch.setattr(
        admin, "settings", dataclasses.replace(settings, admin_ids=frozenset({777}))
    )
    reload_mock = AsyncMock(return_value="Тексты обновлены ✅")
    monkeypatch.setattr(admin.text_overrides, "reload", reload_mock)
    message = _message(777)

    await admin.reload_texts(message)

    reload_mock.assert_awaited_once()
    message.answer.assert_awaited_once_with("🔁 Тексты обновлены ✅")


async def test_reload_is_silent_for_non_admin(monkeypatch):
    monkeypatch.setattr(
        admin, "settings", dataclasses.replace(settings, admin_ids=frozenset({777}))
    )
    reload_mock = AsyncMock()
    monkeypatch.setattr(admin.text_overrides, "reload", reload_mock)
    message = _message(999)

    await admin.reload_texts(message)

    reload_mock.assert_not_awaited()
    message.answer.assert_not_awaited()


async def test_reload_is_silent_for_missing_user(monkeypatch):
    monkeypatch.setattr(
        admin, "settings", dataclasses.replace(settings, admin_ids=frozenset({777}))
    )
    message = _message(None)

    await admin.reload_texts(message)

    message.answer.assert_not_awaited()


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


async def test_status_counts_recent_events_only(monkeypatch, tmp_path):
    log = tmp_path / "interactions.jsonl"
    now = datetime.now(timezone.utc)
    recent = (now - timedelta(days=1)).isoformat()
    old = (now - timedelta(days=10)).isoformat()  # outside the 7-day window
    lines = [
        json.dumps({"ts": recent, "event": "start"}),
        json.dumps({"ts": recent, "event": "start"}),
        json.dumps({"ts": recent, "event": "magnet_delivered"}),
        json.dumps({"ts": recent, "event": "handoff"}),
        json.dumps({"ts": old, "event": "start"}),
        json.dumps({"ts": recent, "event": "tap"}),  # not counted by /status
        json.dumps({"ts": "not-a-timestamp", "event": "start"}),  # bad ts, skipped
        "not valid json at all {",  # malformed line, skipped
    ]
    log.write_text("\n".join(lines) + "\n", encoding="utf-8")
    monkeypatch.setattr(
        admin,
        "settings",
        dataclasses.replace(
            settings, admin_ids=frozenset({777}), interaction_log_path=str(log)
        ),
    )
    message = _message(777)

    await admin.cmd_status(message)

    message.answer.assert_awaited_once()
    body = message.answer.call_args.args[0]
    assert "Переходов в бот: 2" in body
    assert "Практик выдано: 1" in body
    assert "Подписок: 0" in body
    assert "Отписок: 0" in body
    assert "Обращений к Артёму: 1" in body


async def test_status_is_silent_for_non_admin(monkeypatch, tmp_path):
    monkeypatch.setattr(
        admin,
        "settings",
        dataclasses.replace(
            settings,
            admin_ids=frozenset({777}),
            interaction_log_path=str(tmp_path / "interactions.jsonl"),
        ),
    )
    message = _message(999)

    await admin.cmd_status(message)

    message.answer.assert_not_awaited()


async def test_status_is_silent_for_missing_user(monkeypatch):
    monkeypatch.setattr(
        admin, "settings", dataclasses.replace(settings, admin_ids=frozenset({777}))
    )
    message = _message(None)

    await admin.cmd_status(message)

    message.answer.assert_not_awaited()


def test_weekly_summary_handles_missing_log_file(monkeypatch, tmp_path):
    monkeypatch.setattr(
        admin,
        "settings",
        dataclasses.replace(
            settings, interaction_log_path=str(tmp_path / "nope.jsonl")
        ),
    )
    assert admin._weekly_summary() == "нет данных (лог пуст)"
