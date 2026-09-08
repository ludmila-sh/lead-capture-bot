from __future__ import annotations

import pytest

from src.content import texts
from src.content.texts import validate_texts


@pytest.fixture(autouse=True)
def _restore_texts():
    """apply_overrides swaps a module global — put it back after each test."""
    saved = texts.current()
    yield
    texts._current = saved


def test_default_segment_exists():
    assert texts.DEFAULT_SEGMENT in texts.LEAD_MAGNETS


def test_expected_segments_present():
    assert {"base", "spina", "office", "mama", "trener"} <= set(texts.LEAD_MAGNETS)
    assert "sheya" not in texts.LEAD_MAGNETS  # renamed to "office"


def test_every_magnet_has_fields():
    for magnet in texts.LEAD_MAGNETS.values():
        assert magnet.label and magnet.text and magnet.question
        if magnet.link:
            assert magnet.link.startswith("http")
        # link is surfaced on a button, so it must NOT be baked into the text
        assert "{link}" not in magnet.text


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("spina", "spina"),
        ("  SPINA ", "spina"),
        ("Mama", "mama"),
        ("office", "office"),
        ("sheya", None),  # old key, renamed
        ("спина", None),  # cyrillic never a valid start param
        ("", None),
        (None, None),
        ("unknown", None),
    ],
)
def test_find_segment(raw, expected):
    assert texts.find_segment(raw) == expected


def test_lead_magnet_falls_back_to_default():
    assert texts.lead_magnet("spina") is texts.LEAD_MAGNETS["spina"]
    assert texts.lead_magnet(None) is texts.LEAD_MAGNETS[texts.DEFAULT_SEGMENT]
    assert texts.lead_magnet("nope") is texts.LEAD_MAGNETS[texts.DEFAULT_SEGMENT]


def test_faq_shape():
    assert 3 <= len(texts.FAQ) <= 5
    for question, answer in texts.FAQ:
        assert question and answer


def test_handoff_template_keeps_placeholders():
    for token in ("{name}", "{contact}", "{user_id}", "{segment}", "{reason}"):
        assert token in texts.HANDOFF_TO_EXPERT


# --- validation --------------------------------------------------------------

_MINIMAL = {
    "default_segment": "base",
    "buttons": {k: "x" for k in texts._REQUIRED_BUTTONS},
    "screens": {k: "x" for k in texts._REQUIRED_SCREENS},
    "lead_magnets": {
        "base": {"label": "B", "link": "", "text": "t", "question": "q"},
    },
    "faq": [{"q": "a", "a": "b"}] * 3,
    "health_keywords": ["боль"],
}


def test_validate_accepts_minimal():
    validate_texts(_MINIMAL)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.pop("default_segment"),
        lambda d: d["screens"].pop("greeting"),
        lambda d: d["buttons"].pop("practice"),
        lambda d: d.update(lead_magnets={}),
        lambda d: d["lead_magnets"]["base"].pop("question"),
        lambda d: d["lead_magnets"]["base"].update(text="see {link} here"),
        lambda d: d.update(faq=[{"q": "x", "a": "y"}]),  # too few
        lambda d: d.update(health_keywords=[]),
        lambda d: d.update(default_segment="ghost"),
    ],
)
def test_validate_rejects_broken(mutate):
    import copy

    data = copy.deepcopy(_MINIMAL)
    mutate(data)
    with pytest.raises(RuntimeError):
        validate_texts(data)


# --- live overrides --------------------------------------------------------


def test_apply_overrides_swaps_values():
    applied = texts.apply_overrides(
        {
            "screens.greeting": "новый привет",
            "buttons.practice": "🎁 Практика",
            "lead_magnets.spina.text": "новый текст про спину",
            "faq.1.q": "Новый первый вопрос?",
        }
    )
    assert set(applied) == {
        "screens.greeting",
        "buttons.practice",
        "lead_magnets.spina.text",
        "faq.1.q",
    }
    assert texts.GREETING == "новый привет"
    assert texts.BTN_PRACTICE == "🎁 Практика"
    assert texts.LEAD_MAGNETS["spina"].text == "новый текст про спину"
    assert texts.FAQ[0][0] == "Новый первый вопрос?"


def test_apply_overrides_ignores_unknown_and_blank_keys():
    applied = texts.apply_overrides(
        {"totally.bogus": "x", "screens.greeting": "  ", "lead_magnets.ghost.text": "y"}
    )
    assert applied == []
    assert texts.GREETING != "  "


def test_apply_overrides_rejects_invalid_and_keeps_current():
    before = texts.GREETING
    with pytest.raises(RuntimeError):
        texts.apply_overrides({"default_segment": "nonexistent"})
    assert texts.GREETING == before  # unchanged


def test_module_getattr_reads_live_bundle():
    texts.apply_overrides({"screens.menu_prompt": "меню?"})
    # both access styles see the same swapped value
    assert texts.MENU_PROMPT == "меню?"
    assert texts.current().MENU_PROMPT == "меню?"


@pytest.mark.parametrize(
    "key, ok",
    [
        ("faq.1.a", True),
        ("screens.greeting", True),
        ("buttons.practice", True),
        ("lead_magnets.spina.text", True),
        ("default_segment", True),
        ("  faq.2.q  ", True),
        ("Ключ", False),
        ("Значение", False),
        ("", False),
        ("random.thing", False),
    ],
)
def test_is_override_key(key, ok):
    assert texts.is_override_key(key) is ok
