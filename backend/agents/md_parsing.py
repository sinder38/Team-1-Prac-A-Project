"""Shared low-level helpers for parsing agent Markdown back into schemas.

Kept schema-agnostic (returns validated *strings*, not enum objects) so both the
agents' ``parse_md`` methods and other Markdown parsers can reuse it.
"""

from __future__ import annotations

import re

# A bare number that does not greedily swallow a trailing sentence period.
NUM = r"([\d,]+(?:\.\d+)?)"

_CONF_VALUES = {"Low", "Medium", "High", "Low-Medium"}


def num(text: str) -> float:
    """Parse a possibly comma-grouped number to float."""
    return float(text.replace(",", "").strip())


def first(pattern: str, text: str, flags: int = re.M) -> str | None:
    """Return the first capture group for ``pattern`` in ``text``, or None."""
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else None


def norm_bias(raw: str) -> str:
    """Map free-form archive bias text to a Bias enum value (lossy)."""
    s = (raw or "").lower()
    has_bull, has_bear = "bull" in s, "bear" in s
    if has_bull and has_bear:
        return "Mixed"
    if has_bull:
        return "Bullish"
    if has_bear:
        return "Bearish"
    if "mixed" in s:
        return "Mixed"
    if "neutral" in s:
        return "Neutral"
    return "Uncertain"


def norm_confidence(raw: str) -> str:
    """'MEDIUM' -> 'Medium', 'LOW–MEDIUM' -> 'Low-Medium'; default Medium."""
    s = (raw or "").strip().replace("–", "-").replace("—", "-").title()
    return s if s in _CONF_VALUES else "Medium"


def norm_macro_bias(raw: str) -> str:
    """Map free-form macro bias text to a MacroBias enum value (lossy)."""
    s = (raw or "").lower()
    if "binary" in s:
        return "Binary-risk"
    if "hawk" in s:
        return "Hawkish"
    if "dov" in s:
        return "Dovish"
    return "Neutral"
