"""Tiny in-memory state — just enough to give the expert useful handoff context.

Not persisted: on restart it is empty, which is acceptable for MVP handoff.
A real store lands with logging/DB work later.
"""

from __future__ import annotations

# user_id -> segment key the user entered through (e.g. "spina").
last_segment: dict[int, str] = {}


def remember_segment(user_id: int, segment: str) -> None:
    last_segment[user_id] = segment


def segment_of(user_id: int) -> str | None:
    return last_segment.get(user_id)
