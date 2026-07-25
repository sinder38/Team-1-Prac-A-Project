"""Parse /data agent Markdown archives into structured JSON payloads.

Each function returns an ``asdict``-shaped dict matching the agent's schema, so
``server.db.rehydrate`` can rebuild the dataclass. These files were produced by
the agents' renderers, so the formats are deterministic; ``W22``/``W23`` follow
the same format with minor drift, covered by the parser tests.
"""

from __future__ import annotations

import re
from datetime import date, datetime


# A bare number, not greedily swallowing a trailing sentence period.
_NUM = r"([\d,]+(?:\.\d+)?)"

_BIAS_VALUES = {"Bullish", "Bearish", "Neutral", "Mixed", "Uncertain"}
_CONF_VALUES = {"Low", "Medium", "High", "Low-Medium"}
_MACRO_BIAS_VALUES = {"Hawkish", "Dovish", "Neutral", "Binary-risk"}


def _num(text: str) -> float:
    return float(text.replace(",", "").strip())


def _first(pattern: str, text: str, flags: int = re.M) -> str | None:
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else None


def _norm_bias(raw: str) -> str:
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


def _norm_confidence(raw: str) -> str:
    """'MEDIUM' -> 'Medium', 'LOW–MEDIUM' -> 'Low-Medium'; default Medium."""
    s = (raw or "").strip().replace("–", "-").replace("—", "-").title()
    return s if s in _CONF_VALUES else "Medium"


def _norm_macro_bias(raw: str) -> str:
    s = (raw or "").lower()
    if "binary" in s:
        return "Binary-risk"
    if "hawk" in s:
        return "Hawkish"
    if "dov" in s:
        return "Dovish"
    return "Neutral"


# --- technical ---------------------------------------------------------------

_TECH_TICKER_RE = re.compile(r"INSTRUMENT:.*?\(([A-Z]+)\)")


def parse_technical(text: str, prediction_date: date) -> dict:
    instruments: dict[str, dict] = {}
    blocks = re.split(r"(?=INSTRUMENT:)", text)
    for block in blocks:
        m = _TECH_TICKER_RE.search(block)
        if not m:
            continue
        ticker = m.group(1)
        try:
            instruments[ticker] = {
                "last_close": _num(_first(rf"LAST CLOSE:\s*{_NUM}", block) or ""),
                "ema_8": _num(_first(rf"8 EMA (?:at|estimated at) ~{_NUM}", block) or ""),
                "ema_21": _num(_first(rf"21 EMA (?:at|estimated at) ~{_NUM}", block) or ""),
                "trend_bias": _norm_bias(_first(r"TECHNICAL BIAS:\s*([A-Za-z -]+)", block) or ""),
                "key_support": _num(_first(rf"Support 1:\s*{_NUM}", block) or ""),
                "key_resistance": _num(_first(rf"Resistance 1:\s*{_NUM}", block) or ""),
                "confidence": _norm_confidence(_first(r"CONFIDENCE:\s*([A-Za-z–—-]+)", block) or ""),
            }
        except ValueError as exc:
            raise ValueError(f"technical: bad number for {ticker}: {exc}") from exc
    if not instruments:
        raise ValueError("technical: no instrument blocks parsed")
    return {
        "prediction_date": prediction_date.isoformat(),
        "instruments": instruments,
        "agent_type": "technical",
    }


# --- macro -------------------------------------------------------------------

_COMMODITY_RE = {
    "wti_oil": r"WTI Crude Oil:\s*([\d,\.]+),\s*weekly change\s*([+-]?[\d.]+)%,\s*direction:\s*(\w+)",
    "gold": r"Gold:\s*([\d,\.]+),\s*weekly change\s*([+-]?[\d.]+)%,\s*direction:\s*(\w+)",
    "dxy": r"DXY \(Dollar\):\s*([\d,\.]+),\s*weekly change\s*([+-]?[\d.]+)%,\s*direction:\s*(\w+)",
}

_CAL_RE = re.compile(
    r"^-\s*(?P<date_label>.+?):\s*(?P<name>.+?)\s*—\s*Expected:\s*(?P<expected>.*?),"
    r"\s*Previous:\s*(?P<previous>.*?)\s*—\s*(?:IMPORTANCE|Impact):\s*(?P<impact>[A-Za-z]+)",
    re.M,
)


def _commodity(text: str, pattern: str) -> dict:
    m = re.search(pattern, text)
    if not m:
        return {"price": 0.0, "weekly_change": 0.0, "direction": ""}
    return {
        "price": _num(m.group(1)),
        "weekly_change": float(m.group(2)),
        "direction": m.group(3),
    }


def _bullets(text: str, header: str) -> list[str]:
    """Collect '- ' bullet lines under a section header up to the next header."""
    lines = text.splitlines()
    out: list[str] = []
    capturing = False
    for line in lines:
        if header in line:
            capturing = True
            continue
        if capturing:
            stripped = line.strip()
            if stripped.startswith("- "):
                out.append(stripped)
            elif stripped and stripped[0].isupper() and stripped.endswith(":"):
                break
            elif re.match(r"^[A-Z][A-Z &/]+", stripped) and ":" in stripped:
                break
    return out


def parse_macro(text: str, prediction_date: date) -> dict:
    fomc_raw = _first(r"Next FOMC date:\s*([A-Za-z]+ \d+, \d{4})", text)
    next_fomc = None
    if fomc_raw:
        try:
            next_fomc = datetime.strptime(fomc_raw, "%B %d, %Y").date().isoformat()
        except ValueError:
            next_fomc = None

    yields = re.search(
        r"2-year yield:\s*([\d.]+)%\s*10-year yield:\s*([\d.]+)%\s*30-year yield:\s*([\d.]+)%",
        text,
    )

    calendar = [
        {
            "date_label": m.group("date_label").strip(),
            "name": m.group("name").strip(),
            "impact": m.group("impact").strip(),
            "expected": m.group("expected").strip() or "N/A",
            "previous": m.group("previous").strip() or "N/A",
            "priority": 0,
            "source_url": "",
        }
        for m in _CAL_RE.finditer(text)
    ]

    return {
        "prediction_date": prediction_date.isoformat(),
        "fed_rate": _first(r"Current Fed rate:\s*(.+)", text) or "",
        "yield_2y": float(yields.group(1)) if yields else 0.0,
        "yield_10y": float(yields.group(2)) if yields else 0.0,
        "yield_30y": float(yields.group(3)) if yields else 0.0,
        "dxy": _commodity(text, _COMMODITY_RE["dxy"]),
        "wti_oil": _commodity(text, _COMMODITY_RE["wti_oil"]),
        "gold": _commodity(text, _COMMODITY_RE["gold"]),
        "macro_bias": _norm_macro_bias(_first(r"MACRO BIAS:\s*(.+)", text) or ""),
        "primary_driver": (_first(r"PRIMARY DRIVER THIS WEEK:\s*(.+)", text) or "").strip(),
        "confidence": _norm_confidence(_first(r"^CONFIDENCE:\s*([A-Za-z–—-]+)", text) or ""),
        "invalidation": _first(r"INVALIDATION:\s*(.+)", text) or "",
        "next_fomc_date": next_fomc,
        "hold_probability": float(_first(r"Hold probability:\s*([\d.]+)%", text) or 0.0),
        "cut_probability": float(_first(r"Cut probability:\s*([\d.]+)%", text) or 0.0),
        "fomc_direction": _first(r"Direction vs last week:\s*(.+)", text) or "N/A",
        "yield_curve": _first(r"Yield curve:\s*([A-Za-z]+)", text) or "N/A",
        "yield_10y_direction": _first(r"10-year direction this week:\s*(\w+)", text) or "N/A",
        "week_ahead_calendar": calendar,
        "key_earnings": _bullets(text, "KEY EARNINGS"),
        "confirmed_news": _bullets(text, "CONFIRMED NEWS"),
        "agent_type": "macro",
    }


# --- almanac -----------------------------------------------------------------

_SECTOR_RE = re.compile(r"^-\s*(?P<sector>.+?):\s*(?P<window>.+?)\s*Bias:\s*(?P<bias>\w+)", re.M)


def parse_almanac(text: str, prediction_date: date) -> dict:
    seasonal = _norm_bias(_first(r"ALMANAC SEASONAL BIAS:\s*(.+)", text) or "")
    thesis = _first(r'ALMANAC THESIS:\s*"?(.+?)"?\s*$', text) or ""

    sectors = [
        {
            "sector": m.group("sector").strip(),
            "bias": _norm_bias(m.group("bias")),
            "window": m.group("window").strip().rstrip("."),
        }
        for m in _SECTOR_RE.finditer(_sector_section(text))
    ]

    return {
        "prediction_date": prediction_date.isoformat(),
        # The archives carry no explicit monthly bias; fall back to seasonal.
        "monthly_bias": seasonal,
        "seasonal_bias": seasonal,
        "confidence": _norm_confidence(_first(r"PATTERN CONFIDENCE:\s*([A-Za-z–—-]+)", text) or ""),
        "thesis": thesis,
        "weekly_pattern": _first(r"SPECIFIC WEEK PATTERN\s*\((.+?)\)", text) or "",
        "sector_signals": sectors,
        "agent_type": "almanac",
    }


def _sector_section(text: str) -> str:
    m = re.search(r"SECTOR SIGNALS:\s*\n(.*?)(?:\n[A-Z][A-Z ]+:|\Z)", text, re.S)
    return m.group(1) if m else ""


# --- evidence ----------------------------------------------------------------


def parse_evidence(text: str, prediction_date: date, week_stem: str) -> dict:
    return {
        "prediction_date": prediction_date.isoformat(),
        "week": week_stem,
        "content": text,
        "agent_type": "evidence",
    }
