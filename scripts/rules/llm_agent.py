"""
Rules for llm_agent output format.

Format reference: data/formats/llm_agent.md
This file is a prompt template — these rules validate the LLM *response*,
i.e. what the LLMs produce when given that prompt. The required output
structure is numbered 1–8 as defined in the template.

Observed LLM variation tolerated by these rules:
- Trailing colon on section headers is optional (Claude omits it)
- Bullet character may be -, ·, •, or * (varies by LLM)
- Item 6 sub-lines (SPX/NDX/IWM) appear after the "6." header line, not on it
- Arrow between item number and label may be ->, ->, or → (Claude uses →)
- Percentage range may or may not be wrapped in brackets
- IWM range may start with 0.0% (no sign prefix)
"""

import re
from typing import List

from .base import BulletRange, FieldValue, Rule, SectionPresent

REGIME_VALUES = {"BULLISH", "BEARISH", "NEUTRAL", "UNCERTAIN", "MIXED"}
CONFIDENCE_VALUES = {"LOW", "MEDIUM", "HIGH"}

# Matches signed or zero percentage: +1.2%, -0.5%, 0.0%
_PCT = r"[+\-]?\d+\.\d+%"
# Full range: "+0.3% to +1.2%" optionally bracketed
PCT_RANGE_PATTERN = re.compile(rf"\[?{_PCT}\s+to\s+{_PCT}\]?")

# Section header: "3. Key Supporting Evidence" with optional trailing colon
_SEC = lambda n, label: re.compile(  # noqa: E731
    rf"^{n}\.\s+{re.escape(label)}:?", re.IGNORECASE
)


RULES: List[Rule] = [
    # ── Item 1: Weekly Regime ─────────────────────────────────────────────
    FieldValue(
        name="1. Weekly Regime",
        pattern=re.compile(
            r"^1\.\s+Weekly Regime:\s+(?P<val>Bullish|Bearish|Neutral|Uncertain|Mixed)",
            re.IGNORECASE,
        ),
        required=True,
        value_validator=lambda m: m.group("val").upper() in REGIME_VALUES,
        value_hint=f"must be one of: {', '.join(sorted(REGIME_VALUES))}",
    ),

    # ── Item 2: Confidence Score ──────────────────────────────────────────
    FieldValue(
        name="2. Confidence Score",
        pattern=re.compile(
            r"^2\.\s+Confidence Score:\s+(?P<val>Low|Medium|High)",
            re.IGNORECASE,
        ),
        required=True,
        value_validator=lambda m: m.group("val").upper() in CONFIDENCE_VALUES,
        value_hint=f"must be one of: {', '.join(sorted(CONFIDENCE_VALUES))}",
    ),

    # ── Item 3: Key Supporting Evidence (≤3 points) ───────────────────────
    SectionPresent(
        name="3. Key Supporting Evidence header",
        header=_SEC(3, "Key Supporting Evidence"),
        required=True,
    ),
    BulletRange(
        name="3. Key Supporting Evidence — 1 to 3 bullets",
        section_header=_SEC(3, "Key Supporting Evidence"),
        bullet_pattern=re.compile(r"^\s*[-·•*]\s+\S"),
        min_count=1,
        max_count=3,
        required=True,
    ),

    # ── Item 4: Key Contradictions (≤2 points) ────────────────────────────
    SectionPresent(
        name="4. Key Contradictions header",
        header=_SEC(4, "Key Contradictions"),
        required=True,
    ),
    BulletRange(
        name="4. Key Contradictions — 1 to 2 bullets",
        section_header=_SEC(4, "Key Contradictions"),
        bullet_pattern=re.compile(r"^\s*[-·•*]\s+\S"),
        min_count=1,
        max_count=2,
        required=True,
    ),

    # ── Item 5: Invalidation Conditions ──────────────────────────────────
    FieldValue(
        name="5. Invalidation Conditions",
        pattern=re.compile(r"^5\.\s+Invalidation Conditions?:?\s+\S", re.IGNORECASE),
        label_pattern=re.compile(r"^5\.\s+Invalidation Conditions?:?\s*$", re.IGNORECASE),
        required=True,
    ),

    # ── Item 6: Predicted % moves ─────────────────────────────────────────
    # The "6." header line introduces the section; SPX/NDX/IWM follow as sub-lines.
    SectionPresent(
        name="6. Predicted % move header",
        header=re.compile(r"^6\.\s+Predicted\s+%\s*move", re.IGNORECASE),
        required=True,
    ),
    FieldValue(
        name="6. Predicted % move — SPX",
        pattern=re.compile(
            rf"(?i)^.*SPX[^:]*:.*{PCT_RANGE_PATTERN.pattern}"
        ),
        required=True,
    ),
    FieldValue(
        name="6. Predicted % move — NDX",
        pattern=re.compile(
            rf"(?i)^.*NDX[^:]*:.*{PCT_RANGE_PATTERN.pattern}"
        ),
        required=True,
    ),
    FieldValue(
        name="6. Predicted % move — IWM",
        pattern=re.compile(
            rf"(?i)^.*IWM[^:]*:.*{PCT_RANGE_PATTERN.pattern}"
        ),
        required=True,
    ),

    # ── Item 7: Plain-English brief ───────────────────────────────────────
    FieldValue(
        name="7. Plain-English brief header",
        pattern=re.compile(r"^7\.\s+Plain-English brief:?", re.IGNORECASE),
        label_pattern=re.compile(r"^7\.\s+Plain-English brief:?\s*$", re.IGNORECASE),
        required=True,
    ),

    # ── Item 8: Disclaimer ────────────────────────────────────────────────
    FieldValue(
        name="8. Disclaimer",
        pattern=re.compile(r"^8\.\s+Disclaimer:?", re.IGNORECASE),
        label_pattern=re.compile(r"^8\.\s+Disclaimer:?\s*$", re.IGNORECASE),
        required=True,
    ),
]
