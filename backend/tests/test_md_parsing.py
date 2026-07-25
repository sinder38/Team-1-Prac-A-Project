"""Unit tests for the shared Markdown-parsing helpers (agents/md_parsing.py)."""

import re

import pytest

from agents import md_parsing as md


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Bullish", "Bullish"),
        ("BEARISH.", "Bearish"),
        ("Cautiously bearish-neutral", "Bearish"),  # bear wins the keyword scan
        ("bull and bear", "Mixed"),
        ("Mixed", "Mixed"),
        ("Neutral", "Neutral"),
        ("", "Uncertain"),
        ("something else", "Uncertain"),
    ],
)
def test_norm_bias(raw, expected):
    assert md.norm_bias(raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("MEDIUM", "Medium"),
        ("high", "High"),
        ("Low", "Low"),
        ("LOW-MEDIUM", "Low-Medium"),
        ("LOW–MEDIUM", "Low-Medium"),  # en dash
        ("LOW—MEDIUM", "Low-Medium"),  # em dash
        ("", "Medium"),  # default
        ("garbage", "Medium"),  # unknown -> default
    ],
)
def test_norm_confidence(raw, expected):
    assert md.norm_confidence(raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Binary-risk", "Binary-risk"),
        ("binary risk (fed hold)", "Binary-risk"),
        ("Hawkish", "Hawkish"),
        ("dovish tilt", "Dovish"),
        ("Neutral", "Neutral"),
        ("", "Neutral"),  # default
    ],
)
def test_norm_macro_bias(raw, expected):
    assert md.norm_macro_bias(raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("7,501", 7501.0),
        ("276.49", 276.49),
        ("  1,234.5  ", 1234.5),
    ],
)
def test_num(raw, expected):
    assert md.num(raw) == expected


def test_num_rejects_non_number():
    with pytest.raises(ValueError):
        md.num("")


def test_first_returns_stripped_group_or_none():
    assert md.first(r"X:\s*(.+)", "X:  hello  ") == "hello"
    assert md.first(r"Y:\s*(.+)", "no match here") is None


def test_num_regex_stops_before_trailing_period():
    # NUM must not swallow the sentence-ending period after a level.
    m = re.search(rf"Support 1:\s*{md.NUM}", "Support 1: 276.49.")
    assert m and md.num(m.group(1)) == 276.49
