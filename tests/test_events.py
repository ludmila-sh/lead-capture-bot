from __future__ import annotations

from types import SimpleNamespace

from src import events
from tests.conftest import read_events


def _user(user_id=555, username="lead", full_name="Лид Лидов"):
    return SimpleNamespace(id=user_id, username=username, full_name=full_name)


def test_user_key_is_stable_and_distinct():
    key_a = events._user_key(111)
    key_b = events._user_key(111)
    key_c = events._user_key(222)

    assert key_a == key_b  # same input -> same key, every time
    assert key_a != key_c  # different users -> different keys
    assert "111" not in key_a  # not just the id in disguise
    assert key_a and len(key_a) == 10


def test_user_key_handles_missing_user():
    assert events._user_key(None) == ""


def test_log_event_survives_jsonl_write_failure(monkeypatch, tmp_path):
    # A path whose "parent" is actually a file: mkdir(parents=True) must raise.
    blocker = tmp_path / "not_a_dir"
    blocker.write_text("x", encoding="utf-8")
    monkeypatch.setattr(events, "_LOG_PATH", blocker / "sub" / "interactions.jsonl")

    # Must not raise even though the write itself fails.
    events.log_event("start", _user(), segment="spina")


def test_log_event_survives_sheets_enqueue_failure(monkeypatch, interaction_log):
    def _boom(*args, **kwargs):
        raise RuntimeError("sheets is down")

    monkeypatch.setattr(events.sheets, "enqueue", _boom)
    # Must not raise, and the JSONL write must still go through first.
    events.log_event("start", _user(), segment="spina")
    assert read_events(interaction_log)[0]["event"] == "start"
