"""Client-facing text.

`texts.yaml` is the bundled source (edit there — no Python). It is parsed and
validated at import into an immutable `Texts` bundle held in `_current`.

Handlers read `texts.GREETING`, `texts.LEAD_MAGNETS`, ... — those names resolve
through `__getattr__` to the live `_current`, so a reload swaps every value at
once. `apply_overrides()` (called by `src.text_overrides` from a Google Sheet)
merges `key -> value` pairs over the bundled YAML and swaps `_current`, keeping
the previous bundle if the result fails validation.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import yaml

_YAML_PATH = Path(__file__).with_name("texts.yaml")

# Optional portrait shown with the plain /start greeting (not the deep-link flow).
_PHOTO_PATH = Path(__file__).parent / "assets" / "artem.jpg"
GREETING_PHOTO: Path | None = _PHOTO_PATH if _PHOTO_PATH.is_file() else None

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
# Dotted keys an override sheet may set (prefixes for nested, exact for scalars).
_OVERRIDE_PREFIXES = ("screens.", "buttons.", "lead_magnets.", "faq.")
_OVERRIDE_SCALARS = {"default_segment"}


def is_override_key(key: str) -> bool:
    """True if `key` is a recognised dotted override key (e.g. 'faq.1.a')."""
    key = (key or "").strip()
    return key in _OVERRIDE_SCALARS or key.startswith(_OVERRIDE_PREFIXES)


@dataclass(frozen=True)
class LeadMagnet:
    label: str  # human name for logs / handoff context, e.g. "Спина"
    link: str  # video URL — appended under the text (shows a preview card)
    video: str  # optional Telegram file_id / .mp4 URL — sent as a video instead
    text: str  # message body
    question: str  # open question for Artyom's script (bot does NOT send it)


@dataclass(frozen=True)
class Texts:
    DEFAULT_SEGMENT: str
    LEAD_MAGNETS: dict[str, LeadMagnet]
    FAQ: tuple[tuple[str, str], ...]  # (question, answer); question = button label
    HEALTH_KEYWORDS: tuple[str, ...]
    GREETING: str
    MENU_PROMPT: str
    FAQ_INTRO: str
    EXPERT: str
    HANDOFF_ACK: str
    HEALTH_REPLY: str
    FALLBACK: str
    HANDOFF_TO_EXPERT: str
    BTN_PRACTICE: str
    BTN_FAQ: str
    BTN_EXPERT: str
    BTN_SUBSCRIBE: str
    BTN_WRITE_EXPERT: str
    BTN_BACK_TO_MENU: str
    BTN_BACK_TO_FAQ: str


def load_texts(path: Path = _YAML_PATH) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def validate_texts(data: object) -> None:
    """Raise RuntimeError with a clear message if the texts are unusable."""
    if not isinstance(data, dict):
        raise RuntimeError("texts: top level must be a mapping")

    missing_screens = _REQUIRED_SCREENS - set((data.get("screens") or {}))
    if missing_screens:
        raise RuntimeError(f"texts: screens missing keys: {sorted(missing_screens)}")

    missing_buttons = _REQUIRED_BUTTONS - set((data.get("buttons") or {}))
    if missing_buttons:
        raise RuntimeError(f"texts: buttons missing keys: {sorted(missing_buttons)}")

    magnets = data.get("lead_magnets")
    if not isinstance(magnets, dict) or not magnets:
        raise RuntimeError("texts: lead_magnets must be a non-empty mapping")
    for key, magnet in magnets.items():
        for field in ("label", "link", "text", "question"):
            if field not in magnet:
                raise RuntimeError(f"texts: lead_magnets.{key} missing '{field}'")
        if "{link}" in magnet["text"]:
            raise RuntimeError(
                f"texts: lead_magnets.{key}.text must not contain '{{link}}' "
                "— the link is appended automatically"
            )

    default = data.get("default_segment")
    if default not in magnets:
        raise RuntimeError(
            f"texts: default_segment {default!r} is not one of {sorted(magnets)}"
        )

    faq = data.get("faq")
    if not isinstance(faq, list) or not (3 <= len(faq) <= 5):
        raise RuntimeError("texts: faq must be a list of 3–5 items")
    for item in faq:
        if not item.get("q") or not item.get("a"):
            raise RuntimeError("texts: every faq item needs non-empty 'q' and 'a'")

    if not data.get("health_keywords"):
        raise RuntimeError("texts: health_keywords must be a non-empty list")


def _build(data: dict) -> Texts:
    validate_texts(data)
    s, b = data["screens"], data["buttons"]
    magnets = {
        key: LeadMagnet(
            label=m["label"],
            link=m["link"],
            video=m.get("video", ""),
            text=m["text"],
            question=m["question"],
        )
        for key, m in data["lead_magnets"].items()
    }
    return Texts(
        DEFAULT_SEGMENT=data["default_segment"],
        LEAD_MAGNETS=magnets,
        FAQ=tuple((i["q"], i["a"]) for i in data["faq"]),
        HEALTH_KEYWORDS=tuple(str(k).lower() for k in data["health_keywords"]),
        GREETING=s["greeting"],
        MENU_PROMPT=s["menu_prompt"],
        FAQ_INTRO=s["faq_intro"],
        EXPERT=s["expert"],
        HANDOFF_ACK=s["handoff_ack"],
        HEALTH_REPLY=s["health_reply"],
        FALLBACK=s["fallback"],
        HANDOFF_TO_EXPERT=s["handoff_to_expert"],
        BTN_PRACTICE=b["practice"],
        BTN_FAQ=b["faq"],
        BTN_EXPERT=b["expert"],
        BTN_SUBSCRIBE=b["subscribe"],
        BTN_WRITE_EXPERT=b["write_expert"],
        BTN_BACK_TO_MENU=b["back_to_menu"],
        BTN_BACK_TO_FAQ=b["back_to_faq"],
    )


_YAML_DATA = load_texts()  # pristine base for merging overrides
_current = _build(_YAML_DATA)


def current() -> Texts:
    return _current


def find_segment(raw: str | None) -> str | None:
    """Return a known segment key for a /start parameter, or None if unknown."""
    key = (raw or "").strip().lower()
    return key if key in _current.LEAD_MAGNETS else None


def lead_magnet(segment: str | None) -> LeadMagnet:
    """Resolve a segment key to its LeadMagnet, falling back to the default."""
    magnets = _current.LEAD_MAGNETS
    return magnets.get(segment or "", magnets[_current.DEFAULT_SEGMENT])


def _set_dotted(data: dict, dotted: str, value: str) -> None:
    parts = dotted.split(".")
    node: object = data
    for part in parts[:-1]:
        node = node[int(part) - 1] if part.isdigit() else node[part]
    last = parts[-1]
    if last.isdigit():
        node[int(last) - 1] = value
    else:
        node[last] = value


def apply_overrides(overrides: Mapping[str, str]) -> list[str]:
    """Merge `key -> value` overrides over the bundled YAML and swap the live
    texts. Returns the applied keys. Raises RuntimeError (keeping the current
    texts) if the merged result fails validation.
    """
    global _current
    data = copy.deepcopy(_YAML_DATA)
    applied: list[str] = []
    for key, value in overrides.items():
        key = key.strip()
        if not (value or "").strip():
            continue  # blank override -> keep the bundled default
        if not is_override_key(key):
            continue
        try:
            _set_dotted(data, key, value)
        except (KeyError, IndexError, TypeError):
            continue  # override points at something that isn't there — skip it
        applied.append(key)
    _current = _build(data)  # validates; raises on invalid
    return applied


def __getattr__(name: str):  # PEP 562 — resolve texts.GREETING etc. from _current
    try:
        return getattr(_current, name)
    except AttributeError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
