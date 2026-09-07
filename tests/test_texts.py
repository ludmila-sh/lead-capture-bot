from __future__ import annotations

import pytest

from src.content import texts


def test_default_segment_exists():
    assert texts.DEFAULT_SEGMENT in texts.LEAD_MAGNETS


def test_every_magnet_has_link_placeholder_and_fields():
    for key, magnet in texts.LEAD_MAGNETS.items():
        assert magnet.label
        assert magnet.link.startswith("http")
        assert "{link}" in magnet.text, f"{key} text missing {{link}}"


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("spina", "spina"),
        ("  SPINA ", "spina"),
        ("Mama", "mama"),
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
