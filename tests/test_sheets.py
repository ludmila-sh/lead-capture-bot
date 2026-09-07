from __future__ import annotations

import dataclasses

import pytest

from src import sheets
from src.config import settings


def test_enqueue_is_noop_when_disabled():
    assert settings.analytics_enabled is False  # conftest
    before = sheets._queue.qsize()
    sheets.enqueue(
        "start",
        user_id=1,
        username="u",
        name="U",
        segment="spina",
        raw_param="spina",
        reason="",
    )
    assert sheets._queue.qsize() == before


def test_ensure_headers_writes_only_when_missing():
    class FakeWS:
        def __init__(self, row1):
            self._row1 = row1
            self.updates = []

        def row_values(self, n):
            return self._row1

        def update(self, values, rng, value_input_option=None):
            self.updates.append((values, rng))

    missing = FakeWS([])
    sheets._ensure_headers(missing)
    assert missing.updates == [([sheets.COLUMNS], "A1")]

    ok = FakeWS(list(sheets.COLUMNS))
    sheets._ensure_headers(ok)
    assert ok.updates == []


def test_summary_formula_uses_worksheet_name(monkeypatch):
    monkeypatch.setattr(
        sheets,
        "settings",
        dataclasses.replace(settings, analytics_worksheet="Аналитика"),
    )
    formula = sheets._summary_formula()
    assert formula.startswith("=QUERY('Аналитика'!A2:H")
    assert "magnet_delivered" in formula
    assert "handoff" in formula


@pytest.mark.parametrize(
    "exc_factory, needle",
    [
        (lambda g: FileNotFoundError("key not found: secrets/x.json"), "key not found"),
        (lambda g: g.exceptions.SpreadsheetNotFound(), "not found (404)"),
        (lambda g: PermissionError(), "access denied (403)"),
        (lambda g: ValueError("bad json"), "ValueError: bad json"),
    ],
)
def test_explain_messages(exc_factory, needle):
    import gspread

    assert needle in sheets._explain(exc_factory(gspread))
