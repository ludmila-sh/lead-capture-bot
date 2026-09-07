from __future__ import annotations

import json

from src import stats

ROWS = [
    {"event": "start", "user_id": 1, "segment": "spina"},
    {"event": "magnet_delivered", "user_id": 1, "segment": "spina"},
    {"event": "start", "user_id": 2, "segment": "spina"},
    {"event": "handoff", "user_id": 2, "segment": "spina", "reason": "health"},
    {"event": "start", "user_id": 1, "segment": "mama"},  # same user, other segment
    {"event": "tap", "user_id": 9, "target": "faq"},  # ignored
    {"event": "subscribed", "user_id": 3, "segment": "mama"},  # not counted by stats
]


def _write(path, rows):
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def test_collect_counts_and_unique_users(tmp_path):
    log = tmp_path / "i.jsonl"
    _write(log, ROWS)
    report = stats.collect(log)

    assert report["spina"] == {
        "start": 2,
        "magnet_delivered": 1,
        "handoff": 1,
        "unique_users": 2,
    }
    assert report["mama"]["start"] == 1
    assert report["mama"]["unique_users"] == 1
    # "*" holds distinct users across all segments (users 1 and 2), not the sum.
    assert report["*"]["unique_users"] == 2


def test_collect_empty_and_missing(tmp_path):
    assert stats.collect(tmp_path / "nope.jsonl") == {}
    only_untracked = tmp_path / "u.jsonl"
    _write(only_untracked, [{"event": "tap", "user_id": 1}])
    assert stats.collect(only_untracked) == {}


def test_collect_skips_bad_lines(tmp_path):
    log = tmp_path / "i.jsonl"
    log.write_text(
        '{"event": "start", "user_id": 1, "segment": "spina"}\n' "not json\n" "\n",
        encoding="utf-8",
    )
    report = stats.collect(log)
    assert report["spina"]["start"] == 1


def test_rows_total_row(tmp_path):
    log = tmp_path / "i.jsonl"
    _write(log, ROWS)
    rows = stats._rows(stats.collect(log))
    assert rows[0] == [
        "segment",
        "start",
        "magnet_delivered",
        "handoff",
        "unique_users",
    ]
    total = rows[-1]
    assert total[0] == "TOTAL"
    assert total[1] == 3  # starts: spina 2 + mama 1
    assert total[-1] == 2  # distinct users overall
