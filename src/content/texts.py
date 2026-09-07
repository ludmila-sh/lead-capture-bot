"""Loader for the client-facing text.

All copy lives in `texts.yaml` (edit there — no Python needed). This module
loads and validates it at import time and exposes the same names the handlers
already use, so nothing else changes when the wording changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

_YAML_PATH = Path(__file__).with_name("texts.yaml")

_REQUIRED_SCREENS = {
    "greeting",
    "menu_prompt",
    "faq_intro",
    "expert",
    "handoff_ack",
    "health_reply",
    "fallback",
    "handoff_to_expert",
}
_REQUIRED_BUTTONS = {
    "practice",
    "faq",
    "expert",
    "subscribe",
    "write_expert",
    "back_to_menu",
    "back_to_faq",
}


@dataclass(frozen=True)
class LeadMagnet:
    label: str  # human name for logs / handoff context, e.g. "Спина"
    link: str  # video URL (may be empty for a link-less soft path)
    text: str  # first message; contains "{link}" when link is set
    question: str  # open follow-up sent right after


def load_texts(path: Path = _YAML_PATH) -> dict:
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    validate_texts(data)
    return data


def validate_texts(data: object) -> None:
    """Raise RuntimeError with a clear message if the texts file is unusable."""
    if not isinstance(data, dict):
        raise RuntimeError("texts.yaml: top level must be a mapping")

    missing_screens = _REQUIRED_SCREENS - set((data.get("screens") or {}))
    if missing_screens:
        raise RuntimeError(
            f"texts.yaml: screens missing keys: {sorted(missing_screens)}"
        )

    missing_buttons = _REQUIRED_BUTTONS - set((data.get("buttons") or {}))
    if missing_buttons:
        raise RuntimeError(
            f"texts.yaml: buttons missing keys: {sorted(missing_buttons)}"
        )

    magnets = data.get("lead_magnets")
    if not isinstance(magnets, dict) or not magnets:
        raise RuntimeError("texts.yaml: lead_magnets must be a non-empty mapping")
    for key, magnet in magnets.items():
        for field in ("label", "link", "text", "question"):
            if field not in magnet:
                raise RuntimeError(f"texts.yaml: lead_magnets.{key} missing '{field}'")
        if magnet["link"] and "{link}" not in magnet["text"]:
            raise RuntimeError(
                f"texts.yaml: lead_magnets.{key}.text has a link but no '{{link}}' placeholder"
            )

    default = data.get("default_segment")
    if default not in magnets:
        raise RuntimeError(
            f"texts.yaml: default_segment {default!r} is not one of {sorted(magnets)}"
        )

    faq = data.get("faq")
    if not isinstance(faq, list) or not (3 <= len(faq) <= 5):
        raise RuntimeError("texts.yaml: faq must be a list of 3–5 items")
    for item in faq:
        if not item.get("q") or not item.get("a"):
            raise RuntimeError("texts.yaml: every faq item needs non-empty 'q' and 'a'")

    if not data.get("health_keywords"):
        raise RuntimeError("texts.yaml: health_keywords must be a non-empty list")


_data = load_texts()

# --- Segments -------------------------------------------------------------
DEFAULT_SEGMENT: str = _data["default_segment"]

LEAD_MAGNETS: dict[str, LeadMagnet] = {
    key: LeadMagnet(
        label=m["label"], link=m["link"], text=m["text"], question=m["question"]
    )
    for key, m in _data["lead_magnets"].items()
}


def find_segment(raw: str | None) -> str | None:
    """Return a known segment key for a /start parameter, or None if unknown."""
    key = (raw or "").strip().lower()
    return key if key in LEAD_MAGNETS else None


def lead_magnet(segment: str | None) -> LeadMagnet:
    """Resolve a segment key to its LeadMagnet, falling back to the default."""
    return LEAD_MAGNETS.get(segment or "", LEAD_MAGNETS[DEFAULT_SEGMENT])


# --- Button labels -----------------------------------------------------------
_b = _data["buttons"]
BTN_PRACTICE: str = _b["practice"]
BTN_FAQ: str = _b["faq"]
BTN_EXPERT: str = _b["expert"]
BTN_SUBSCRIBE: str = _b["subscribe"]
BTN_WRITE_EXPERT: str = _b["write_expert"]
BTN_BACK_TO_MENU: str = _b["back_to_menu"]
BTN_BACK_TO_FAQ: str = _b["back_to_faq"]

# --- Screens ---------------------------------------------------------------
_s = _data["screens"]
GREETING: str = _s["greeting"]
MENU_PROMPT: str = _s["menu_prompt"]
FAQ_INTRO: str = _s["faq_intro"]
EXPERT: str = _s["expert"]
HANDOFF_ACK: str = _s["handoff_ack"]
HEALTH_REPLY: str = _s["health_reply"]
FALLBACK: str = _s["fallback"]
HANDOFF_TO_EXPERT: str = _s["handoff_to_expert"]

# List of (question, answer). Question doubles as the button label.
FAQ: list[tuple[str, str]] = [(item["q"], item["a"]) for item in _data["faq"]]

HEALTH_KEYWORDS: list[str] = [str(k).lower() for k in _data["health_keywords"]]
