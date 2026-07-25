"""Field-level tests for each agent's ``parse_md`` (inverse of ``render_md``).

Covers: every archived week is complete and parses without error; the
prediction date is read from the document; and concrete values parsed from the
real /data archives. A missing artifact for a discovered week is a failure, not
a skip.
"""

from dataclasses import asdict
from datetime import date

import pytest

from agents.almanac.almanac_agent import AlmanacAgent
from agents.evidence.evidence_agent import EvidenceAgent
from core.io import week_stem
from agents.macro.macro_agent import MacroAgent
from agents.paths import DATA_DIR
from core.schemas import Bias, Confidence, MacroBias
from agents.technical.technical_agent import TechnicalAgent
from server.archive import _read_text, _resolve_agent_path, discover_archive_stems

# Discovered from the real /data tree at collection time (Markdown weeks only).
DISCOVERED = discover_archive_stems()
STEMS = sorted(DISCOVERED)

_AGENTS = {
    "technical": TechnicalAgent,
    "macro": MacroAgent,
    "almanac": AlmanacAgent,
}


def _text(agent: str, stem: str) -> str:
    path = _resolve_agent_path(agent, stem)
    assert path is not None, f"missing {agent} archive for {stem}"
    text = _read_text(path)
    assert text, f"empty {agent} archive for {stem}"
    return text


def test_some_weeks_were_discovered():
    assert STEMS, "no archive weeks discovered under /data"


# --- every discovered week must be complete ----------------------------------


@pytest.mark.parametrize("stem", STEMS)
def test_week_has_all_artifacts(stem):
    for agent in ("almanac", "macro", "technical", "evidence"):
        assert _resolve_agent_path(agent, stem) is not None, f"{stem} missing {agent}"
    assert (DATA_DIR / "llm" / f"llm_comparison_{stem}.md").exists(), f"{stem} missing llm comparison"
    assert (DATA_DIR / "human" / f"human_score_{stem}.md").exists(), f"{stem} missing human score"


# --- every discovered week must parse without error --------------------------


@pytest.mark.parametrize("stem", STEMS)
@pytest.mark.parametrize("agent", ["almanac", "macro", "technical", "evidence"])
def test_parse_md_never_errors(agent, stem):
    text = _text(agent, stem)
    cls = EvidenceAgent if agent == "evidence" else _AGENTS[agent]
    # Pass the discovered date as a fallback for files without a recoverable one.
    output = cls.parse_md(text, DISCOVERED[stem])
    assert asdict(output)  # constructs + serializes


# --- prediction date is read from the document (#1) --------------------------


def test_date_extracted_from_technical_header():
    out = TechnicalAgent.parse_md(_text("technical", "W25"))  # no date passed
    assert out.prediction_date == date(2026, 6, 21)  # "Week of 21 June 2026"


def test_date_extracted_from_macro_footer():
    out = MacroAgent.parse_md(_text("macro", "W25"))  # no date passed
    assert out.prediction_date == date(2026, 6, 21)  # "Sources accessed: 2026-06-21"


def test_date_extracted_from_almanac_week_range():
    out = AlmanacAgent.parse_md(_text("almanac", "W25"))  # no date passed
    assert out.prediction_date == date(2026, 6, 15)  # "Week of 15–19 June 2026"


def test_macro_without_recoverable_date_requires_fallback():
    # Older macro files have no "Sources accessed:" footer.
    text = _text("macro", "W22")
    with pytest.raises(ValueError):
        MacroAgent.parse_md(text)  # no date, none in document
    assert MacroAgent.parse_md(text, date(2026, 5, 25)).prediction_date == date(2026, 5, 25)


# --- technical ---------------------------------------------------------------


def test_technical_w25_all_instruments():
    out = TechnicalAgent.parse_md(_text("technical", "W25"))
    assert set(out.instruments) == {"SPX", "NDX", "IWM"}

    spx = out.instruments["SPX"]
    assert (spx.last_close, spx.ema_8, spx.ema_21) == (7501.0, 7464.0, 7443.0)
    assert (spx.key_support, spx.key_resistance) == (7238.0, 7621.0)
    assert spx.trend_bias is Bias.BULLISH
    assert spx.confidence is Confidence.MEDIUM

    ndx = out.instruments["NDX"]
    assert (ndx.last_close, ndx.ema_8, ndx.ema_21) == (30406.0, 29893.0, 29604.0)
    assert (ndx.key_support, ndx.key_resistance) == (28197.0, 30762.0)
    assert ndx.confidence is Confidence.HIGH

    iwm = out.instruments["IWM"]
    # Trailing sentence period must not be swallowed into the number.
    assert (iwm.last_close, iwm.key_support, iwm.key_resistance) == (295.59, 276.49, 297.91)
    assert iwm.confidence is Confidence.HIGH


def test_technical_w22_older_format():
    # W22 uses "8 EMA estimated at ~" and levels with trailing parentheticals.
    out = TechnicalAgent.parse_md(_text("technical", "W22"))
    spx = out.instruments["SPX"]
    assert spx.last_close == 7580.06
    assert spx.ema_8 == 7505.06
    assert spx.ema_21 == 7389.24
    assert spx.key_support == 7516.72
    assert spx.key_resistance == 7600.0  # "7,600.00 (Round number...)"
    assert spx.trend_bias is Bias.BULLISH
    assert spx.confidence is Confidence.HIGH


def test_technical_empty_raises():
    with pytest.raises(ValueError):
        TechnicalAgent.parse_md("Week of 21 June 2026\nno instrument blocks")


# --- macro -------------------------------------------------------------------


def test_macro_w25_scalars():
    out = MacroAgent.parse_md(_text("macro", "W25"))
    assert out.fed_rate == "3.50%-3.75%"
    assert (out.yield_2y, out.yield_10y, out.yield_30y) == (4.2, 4.49, 4.93)
    assert out.next_fomc_date == date(2026, 6, 18)
    assert out.hold_probability == 97.4
    assert out.cut_probability == 2.6
    assert out.fomc_direction == "shifted hawkish slightly"
    assert out.yield_curve == "normal"
    assert out.yield_10y_direction == "falling"


def test_macro_w25_commodities():
    out = MacroAgent.parse_md(_text("macro", "W25"))
    assert (out.dxy.price, out.dxy.weekly_change, out.dxy.direction) == (100.85, 0.99, "rising")
    assert (out.wti_oil.price, out.wti_oil.weekly_change, out.wti_oil.direction) == (76.54, -9.83, "falling")
    assert (out.gold.price, out.gold.weekly_change, out.gold.direction) == (4172.9, -1.0, "falling")


def test_macro_w25_classification():
    out = MacroAgent.parse_md(_text("macro", "W25"))
    assert out.macro_bias is MacroBias.BINARY_RISK
    assert out.primary_driver == "US Fed Interest Rate Decision event on June 18"
    assert out.confidence is Confidence.MEDIUM
    assert "dovish" in out.invalidation.lower()


def test_macro_w25_lists():
    out = MacroAgent.parse_md(_text("macro", "W25"))
    assert len(out.week_ahead_calendar) == 4
    first = out.week_ahead_calendar[0]
    assert first.date_label == "Thursday, June 18"
    assert first.name == "US Fed Interest Rate Decision"
    assert first.expected == "Hold"
    assert first.previous == "3.50%-3.75%"
    assert first.impact == "High"

    assert len(out.key_earnings) == 3
    assert "Accenture" in out.key_earnings[0]
    assert len(out.confirmed_news) == 3


def test_macro_empty_defaults_do_not_raise():
    out = MacroAgent.parse_md("nothing useful", date(2026, 6, 18))
    assert out.fed_rate == ""
    assert out.yield_10y == 0.0
    assert out.macro_bias is MacroBias.NEUTRAL
    assert out.confidence is Confidence.MEDIUM
    assert out.dxy.price == 0.0
    assert out.dxy.direction == ""
    assert out.week_ahead_calendar == []


# --- almanac -----------------------------------------------------------------


def test_almanac_w25_fields():
    out = AlmanacAgent.parse_md(_text("almanac", "W25"))
    assert out.seasonal_bias is Bias.BEARISH
    # No explicit monthly bias in archives -> falls back to seasonal.
    assert out.monthly_bias is Bias.BEARISH
    assert out.confidence is Confidence.MEDIUM
    assert out.thesis.startswith("Mid-June Triple-Witching")
    assert out.weekly_pattern == "Mid-June Week, 15-19 June"


def test_almanac_w25_sectors():
    out = AlmanacAgent.parse_md(_text("almanac", "W25"))
    assert len(out.sector_signals) == 5
    first = out.sector_signals[0]
    assert first.sector == "Technology (XLK)"
    assert first.bias is Bias.BULLISH
    assert "LONG" in first.window


def test_almanac_w22_zero_sectors_is_acceptable():
    # W22's almanac archive has no parseable SECTOR SIGNALS block; that's fine.
    out = AlmanacAgent.parse_md(_text("almanac", "W22"))
    assert out.sector_signals == []


# --- evidence ----------------------------------------------------------------


@pytest.mark.parametrize("stem", STEMS)
def test_evidence_content_and_week(stem):
    text = _text("evidence", stem)
    out = EvidenceAgent.parse_md(text, date(2026, 6, 18))
    assert out.content == text
    assert out.week == week_stem(date(2026, 6, 18))
