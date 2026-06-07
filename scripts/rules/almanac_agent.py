"""
Rules for almanac_agent output format.

Format reference: data/formats/almanac_agent.md
Canonical example has real data — rules are derived from that exact structure.
"""

import re
from typing import List

from .base import BulletCount, FieldValue, LineMatch, Rule, SectionPresent

CONFIDENCE_VALUES = {
    "LOW",
    "MEDIUM",
    "HIGH",
    "LOW-MEDIUM",
    "MEDIUM-HIGH",
    "LOW–MEDIUM",
    "MEDIUM–HIGH",
}

RULES: List[Rule] = [
    # ── Header / preamble ─────────────────────────────────────────────────
    LineMatch(
        name="Title line",
        pattern=re.compile(r"^Almanac Agent Output — Week of .+"),
        line_hint="Line 1",
        required=True,
    ),
    FieldValue(
        name="MONTH field",
        pattern=re.compile(r"^MONTH:\s+\w+ \d{4}$"),
        required=True,
    ),
    FieldValue(
        name="CYCLE CONTEXT field",
        pattern=re.compile(r"^CYCLE CONTEXT:"),
        required=True,
    ),
    # ── MONTHLY STATS section ─────────────────────────────────────────────
    SectionPresent(
        name="MONTHLY STATS section",
        header=re.compile(r"^MONTHLY STATS:"),
        required=True,
    ),
    BulletCount(
        name="MONTHLY STATS — S&P 500 bullet",
        section_header=re.compile(r"^MONTHLY STATS:"),
        bullet_pattern=re.compile(r"^\s*-\s+S&P 500:"),
        min_count=1,
        max_count=1,
        required=True,
    ),
    BulletCount(
        name="MONTHLY STATS — Nasdaq bullet",
        section_header=re.compile(r"^MONTHLY STATS:"),
        bullet_pattern=re.compile(r"^\s*-\s+Nasdaq:"),
        min_count=1,
        max_count=1,
        required=True,
    ),
    BulletCount(
        name="MONTHLY STATS — Russell 2000 bullet",
        section_header=re.compile(r"^MONTHLY STATS:"),
        bullet_pattern=re.compile(r"^\s*-\s+Russell 2000:"),
        min_count=1,
        max_count=1,
        required=True,
    ),
    # ── SPECIFIC WEEK PATTERN ─────────────────────────────────────────────
    SectionPresent(
        name="SPECIFIC WEEK PATTERN section",
        header=re.compile(r"^SPECIFIC WEEK PATTERN\s*\("),
        required=True,
    ),
    # ── SECTOR SIGNALS ────────────────────────────────────────────────────
    SectionPresent(
        name="SECTOR SIGNALS section",
        header=re.compile(r"^SECTOR SIGNALS:"),
        required=True,
    ),
    BulletCount(
        name="SECTOR SIGNALS — at least one sector entry",
        section_header=re.compile(r"^SECTOR SIGNALS:"),
        bullet_pattern=re.compile(
            r"^\s*-\s+\w+.*seasonal\s+(SHORT|LONG)", re.IGNORECASE
        ),
        min_count=1,
        max_count=None,
        required=True,
    ),
    # ── Closing fields ────────────────────────────────────────────────────
    FieldValue(
        name="ALMANAC SEASONAL BIAS field",
        pattern=re.compile(r"^ALMANAC SEASONAL BIAS:\s+\S"),
        label_pattern=re.compile(r"^ALMANAC SEASONAL BIAS:\s*$"),
        required=True,
    ),
    FieldValue(
        name="PATTERN CONFIDENCE field",
        pattern=re.compile(
            r"^PATTERN CONFIDENCE:\s+(?P<val>[A-Z][A-Z\-–]+)",
        ),
        label_pattern=re.compile(r"^PATTERN CONFIDENCE:\s*$"),
        required=True,
        value_validator=lambda m: (
            m.group("val").upper().replace("–", "-") in CONFIDENCE_VALUES
        ),
        value_hint=f"must be one of: {', '.join(sorted(CONFIDENCE_VALUES))}",
    ),
    FieldValue(
        name="ALMANAC THESIS field (quoted)",
        pattern=re.compile(r'^ALMANAC THESIS:\s+"[^"]+"'),
        label_pattern=re.compile(r"^ALMANAC THESIS:\s*$"),
        required=True,
    ),
    FieldValue(
        name="Source citation",
        pattern=re.compile(r"^Source:"),
        required=True,
    ),
]
