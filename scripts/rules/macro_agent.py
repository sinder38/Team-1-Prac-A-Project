"""
Rules for macro_agent output format.

Format reference: data/formats/macro_agent.md
This format uses placeholder fields — rules check structure and label presence,
not specific data values.
"""

import re
from typing import List

from .base import BulletCount, BulletRange, FieldValue, Rule, SectionPresent

MACRO_BIAS_VALUES = {"HAWKISH", "DOVISH", "NEUTRAL", "BINARY-RISK"}
CONFIDENCE_VALUES = {"LOW", "MEDIUM", "HIGH"}
YIELD_CURVE_VALUES = {"NORMAL", "INVERTED", "FLAT"}
IMPORTANCE_VALUES = {"HIGH", "MED", "LOW"}


RULES: List[Rule] = [
    # ── Title ─────────────────────────────────────────────────────────────
    FieldValue(
        name="Title line",
        pattern=re.compile(r"^Macro Agent Output — Week of .+[—\-].+Source: R4"),
        required=True,
    ),
    # ── FED & RATES ───────────────────────────────────────────────────────
    SectionPresent(
        name="FED & RATES section",
        header=re.compile(r"^FED & RATES\s*\("),
        required=True,
    ),
    BulletCount(
        name="FED & RATES — Current Fed rate bullet",
        section_header=re.compile(r"^FED & RATES\s*\("),
        bullet_pattern=re.compile(r"^\s*[·\-]\s+Current Fed rate:"),
        min_count=1,
        max_count=1,
        required=True,
    ),
    BulletCount(
        name="FED & RATES — Next FOMC date bullet",
        section_header=re.compile(r"^FED & RATES\s*\("),
        bullet_pattern=re.compile(r"^\s*[·\-]\s+Next FOMC date:"),
        min_count=1,
        max_count=1,
        required=True,
    ),
    BulletCount(
        name="FED & RATES — FOMC bullet contains Hold and Cut probability",
        section_header=re.compile(r"^FED & RATES\s*\("),
        bullet_pattern=re.compile(
            r"^\s*[·\-]\s+Next FOMC date:.*Hold probability:.*Cut probability:"
        ),
        min_count=1,
        max_count=1,
        required=True,
    ),
    BulletCount(
        name="FED & RATES — yield bullet (2-year, 10-year, 30-year)",
        section_header=re.compile(r"^FED & RATES\s*\("),
        bullet_pattern=re.compile(
            r"^\s*[·\-]\s+2-year yield:.*10-year yield:.*30-year yield:"
        ),
        min_count=1,
        max_count=1,
        required=True,
    ),
    BulletCount(
        name="FED & RATES — Yield curve bullet",
        section_header=re.compile(r"^FED & RATES\s*\("),
        bullet_pattern=re.compile(r"^\s*[·\-]\s+Yield curve:"),
        min_count=1,
        max_count=1,
        required=True,
    ),
    # ── COMMODITIES & DOLLAR ──────────────────────────────────────────────
    SectionPresent(
        name="COMMODITIES & DOLLAR section",
        header=re.compile(r"^COMMODITIES & DOLLAR\s*\("),
        required=True,
    ),
    BulletCount(
        name="COMMODITIES & DOLLAR — WTI Crude Oil bullet",
        section_header=re.compile(r"^COMMODITIES & DOLLAR\s*\("),
        bullet_pattern=re.compile(r"^\s*[·\-]\s+WTI Crude Oil:"),
        min_count=1,
        max_count=1,
        required=True,
    ),
    BulletCount(
        name="COMMODITIES & DOLLAR — Gold bullet",
        section_header=re.compile(r"^COMMODITIES & DOLLAR\s*\("),
        bullet_pattern=re.compile(r"^\s*[·\-]\s+Gold:"),
        min_count=1,
        max_count=1,
        required=True,
    ),
    BulletCount(
        name="COMMODITIES & DOLLAR — DXY bullet",
        section_header=re.compile(r"^COMMODITIES & DOLLAR\s*\("),
        bullet_pattern=re.compile(r"^\s*[·\-]\s+DXY \(Dollar\):"),
        min_count=1,
        max_count=1,
        required=True,
    ),
    # ── WEEK-AHEAD CALENDAR ───────────────────────────────────────────────
    SectionPresent(
        name="WEEK-AHEAD CALENDAR section",
        header=re.compile(r"^WEEK-AHEAD CALENDAR\s*\("),
        required=True,
    ),
    BulletRange(
        name="WEEK-AHEAD CALENDAR — 1 to 5 entries",
        section_header=re.compile(r"^WEEK-AHEAD CALENDAR\s*\("),
        bullet_pattern=re.compile(
            r"^\s*[·\-]\s+\w+,\s+"
        ),  # "- Tuesday, June 2" or "· Mon, 2"
        min_count=1,
        max_count=5,
        required=True,
    ),
    BulletCount(
        name="WEEK-AHEAD CALENDAR — entries include IMPORTANCE/Impact label",
        section_header=re.compile(r"^WEEK-AHEAD CALENDAR\s*\("),
        bullet_pattern=re.compile(
            r"^\s*[·\-].*(?:IMPORTANCE|Impact):\s*(High|Med|Low)", re.IGNORECASE
        ),
        min_count=1,
        max_count=None,
        required=True,
    ),
    # ── KEY EARNINGS ──────────────────────────────────────────────────────
    SectionPresent(
        name="KEY EARNINGS THIS WEEK section",
        header=re.compile(r"^KEY EARNINGS THIS WEEK\s*\("),
        required=True,
    ),
    BulletRange(
        name="KEY EARNINGS — 0 to 5 entries",
        section_header=re.compile(r"^KEY EARNINGS THIS WEEK\s*\("),
        bullet_pattern=re.compile(r"^\s*[·\-]\s+\S"),
        min_count=0,
        max_count=5,
        required=True,
    ),
    # ── CONFIRMED NEWS EVENTS ─────────────────────────────────────────────
    SectionPresent(
        name="CONFIRMED NEWS EVENTS section",
        header=re.compile(r"^CONFIRMED NEWS EVENTS\s*\("),
        required=True,
    ),
    BulletCount(
        name="CONFIRMED NEWS EVENTS — each entry cites Reuters or AP",
        section_header=re.compile(r"^CONFIRMED NEWS EVENTS\s*\("),
        bullet_pattern=re.compile(
            r"^\s*[·\-].*(?:Source:\s*(?:Reuters|AP)\b|No\b.*headlines\b)",
            re.IGNORECASE,
        ),
        min_count=1,
        max_count=None,
        required=True,
    ),
    # ── Closing fields ────────────────────────────────────────────────────
    FieldValue(
        name="MACRO BIAS field",
        pattern=re.compile(r"^MACRO BIAS:\s+(?P<val>\S+)"),
        required=True,
        value_validator=lambda m: (
            m.group("val").upper().rstrip(".") in MACRO_BIAS_VALUES
        ),
        value_hint=f"must be one of: {', '.join(sorted(MACRO_BIAS_VALUES))}",
    ),
    FieldValue(
        name="PRIMARY DRIVER THIS WEEK field",
        pattern=re.compile(r"^PRIMARY DRIVER THIS WEEK:\s+\S"),
        label_pattern=re.compile(r"^PRIMARY DRIVER THIS WEEK:\s*$"),
        required=True,
    ),
    FieldValue(
        name="CONFIDENCE field",
        pattern=re.compile(r"^CONFIDENCE:\s+(?P<val>Low|Medium|High)", re.IGNORECASE),
        label_pattern=re.compile(r"^CONFIDENCE:\s*$"),
        required=True,
        value_validator=lambda m: m.group("val").upper() in CONFIDENCE_VALUES,
        value_hint=f"must be one of: {', '.join(sorted(CONFIDENCE_VALUES))}",
    ),
    FieldValue(
        name="INVALIDATION field",
        pattern=re.compile(r"^INVALIDATION:\s+\S"),
        label_pattern=re.compile(r"^INVALIDATION:\s*$"),
        required=True,
    ),
    FieldValue(
        name="Sources accessed line",
        pattern=re.compile(r"^Sources accessed:"),
        required=True,
    ),
]
