import json
import pytest
from datetime import date
from pathlib import Path

from agents.almanac.almanac_agent import AlmanacAgent
from agents.schemas import AlmanacOutput, Bias, Confidence
from agents.pipeline.context import PipelineContext
from agents.pipeline.stages import run_almanac


def test_week_of_month():
    assert AlmanacAgent._week_of_month(date(2026, 6, 1)) == 1
    assert AlmanacAgent._week_of_month(date(2026, 6, 7)) == 1
    assert AlmanacAgent._week_of_month(date(2026, 6, 8)) == 2
    assert AlmanacAgent._week_of_month(date(2026, 6, 14)) == 2
    assert AlmanacAgent._week_of_month(date(2026, 6, 15)) == 3
    assert AlmanacAgent._week_of_month(date(2026, 6, 21)) == 3
    assert AlmanacAgent._week_of_month(date(2026, 6, 22)) == 4
    assert AlmanacAgent._week_of_month(date(2026, 6, 28)) == 4
    assert AlmanacAgent._week_of_month(date(2026, 6, 29)) == 5
    assert AlmanacAgent._week_of_month(date(2026, 6, 30)) == 5


def test_week_bounds():
    start, end = AlmanacAgent._week_bounds(date(2026, 6, 16))
    assert start == date(2026, 6, 15)
    assert end == date(2026, 6, 19)


def test_format_period():
    period1 = AlmanacAgent._format_period(date(2026, 6, 15), date(2026, 6, 19))
    assert "15" in period1
    assert "19" in period1
    assert "June" in period1
    assert "2026" in period1

    period2 = AlmanacAgent._format_period(date(2026, 6, 29), date(2026, 7, 3))
    assert "29" in period2
    assert "June" in period2
    assert "3" in period2
    assert "July" in period2
    assert "2026" in period2


def test_lookup_seasonal_data_success():
    agent = AlmanacAgent()
    output = agent.lookup_seasonal_data(date(2026, 6, 16))
    #
    # Source: WEEKLY_PATTERNS[(6, 3)] at almanac_data.py:416-435
    #   "name": "Mid-June weakness / CPI follow-through week"
    #   "seasonal_bias": "Bearish"
    #   "confidence": "Medium"
    #   "thesis": "Seasonality is still a headwind in mid-June..."
    #
    # Source: MONTHLY_STATS[6] at almanac_data.py:169-197
    #   "monthly_bias": "Bearish"
    #
    assert isinstance(output, AlmanacOutput)
    assert output.prediction_date == date(2026, 6, 16)
    assert output.monthly_bias == Bias.BEARISH
    assert output.seasonal_bias == Bias.BEARISH
    assert output.confidence == Confidence.MEDIUM
    assert output.weekly_pattern == "Mid-June weakness / Triple-Witching week"
    assert len(output.sector_signals) > 0
    assert "Almanac base case stays cautious" in output.thesis


def test_lookup_seasonal_data_fallback():
    agent = AlmanacAgent()
    output = agent.lookup_seasonal_data(date(2026, 12, 15))
    #
    # Source: MONTHLY_STATS[12] at almanac_data.py:299-317
    #   "monthly_bias": "Bullish"
    #
    # No WEEKLY_PATTERNS entry for (12, 3) — falls back to
    #   "name": "General monthly seasonal pattern"
    #   "seasonal_bias": month_data["monthly_bias"] → "Bullish"
    #   "confidence": "Low"
    #   "thesis": "Only the monthly Almanac context is encoded..."
    #   See _get_week_data() at almanac_agent.py:136-151
    #
    assert isinstance(output, AlmanacOutput)
    assert output.prediction_date == date(2026, 12, 15)
    assert output.monthly_bias == Bias.BULLISH
    assert output.seasonal_bias == Bias.BULLISH
    assert output.confidence == Confidence.LOW
    assert output.weekly_pattern == "General monthly seasonal pattern"
    assert "background input" in output.thesis


def test_run_returns_almanac_output():
    agent = AlmanacAgent()
    output = agent.run(date(2026, 6, 16))
    assert isinstance(output, AlmanacOutput)


def test_render_md():
    agent = AlmanacAgent()
    output = agent.run(date(2026, 6, 16))
    md_content = agent.render_md(output, date(2026, 6, 16))
    assert "Almanac Agent Output" in md_content
    assert "MONTH: June 2026" in md_content
    assert "CYCLE CONTEXT:" in md_content
    assert "MONTHLY STATS:" in md_content
    assert "SPECIFIC WEEK PATTERN" in md_content
    assert "SECTOR SIGNALS:" in md_content
    assert "ALMANAC THESIS:" in md_content
    assert "Source:" in md_content


@pytest.fixture
def setup_integration(tmp_path, monkeypatch):
    monkeypatch.setattr("agents.pipeline.stages.REPO_ROOT", tmp_path)
    monkeypatch.setattr("agents.io.DATA_ROOT", tmp_path / "outputs")
    return tmp_path


def _verify_artifacts(tmp_path, week_str, expected_json, expected_md_contains):
    json_path = tmp_path / "outputs" / "almanac" / f"{week_str}.json"
    assert json_path.exists(), f"JSON output file was not created at {json_path}"
    with open(json_path, "r", encoding="utf-8") as f:
        saved_data = json.load(f)
    for key, value in expected_json.items():
        assert saved_data[key] == value, \
            f"Key '{key}' mismatch in JSON: expected {value}, got {saved_data[key]}"

    md_path = tmp_path / "data" / "almanac" / f"almanac_agent_{week_str}.md"
    assert md_path.exists(), f"Markdown output file was not created at {md_path}"
    md_content = md_path.read_text(encoding="utf-8")
    for substring in expected_md_contains:
        assert substring in md_content, \
            f"Expected substring '{substring}' not found in Markdown content"


def test_almanac_integration_fallback(setup_integration):
    # ---------------------------------------------------------------
    # Fallback scenario: 2026-12-15 is December Week 3 → (12, 3)
    # No WEEKLY_PATTERNS entry exists for (12, 3).
    # Agent falls back to MONTHLY_STATS[12] (almanac_data.py:299-317):
    #   "monthly_bias": "Bullish"
    # Fallback dict (almanac_agent.py:136-151):
    #   "seasonal_bias": month_data["monthly_bias"] → "Bullish"
    #   "confidence": "Low"
    #   "name": "General monthly seasonal pattern"
    #   "thesis": "Only the monthly Almanac context is encoded..."
    # ---------------------------------------------------------------
    tmp_path = setup_integration
    prediction_date = date(2026, 12, 15)
    ctx = PipelineContext(prediction_date=prediction_date)
    config = {"artifacts": {"save_json": True, "save_md": True}}

    run_almanac(ctx, config)

    assert ctx.almanac is not None
    assert ctx.almanac.prediction_date == prediction_date
    assert ctx.almanac.monthly_bias == Bias.BULLISH
    assert ctx.almanac.seasonal_bias == Bias.BULLISH
    assert ctx.almanac.confidence == Confidence.LOW

    _verify_artifacts(
        tmp_path,
        week_str="W51",
        expected_json={
            "prediction_date": "2026-12-15",
            "monthly_bias": "Bullish",
            "seasonal_bias": "Bullish",
            "confidence": "Low",
            "weekly_pattern": "General monthly seasonal pattern",
        },
        expected_md_contains=[
            "MONTH: December 2026",
            "SPECIFIC WEEK PATTERN (December week):",
            "No specific weekly pattern has been encoded yet for this date.",
            "ALMANAC SEASONAL BIAS: Bullish.",
            "PATTERN CONFIDENCE: LOW.",
        ]
    )


def test_almanac_integration_week_1_memorial_day(setup_integration):
    # ---------------------------------------------------------------
    # WEEKLY_PATTERNS[(5, 4)] at almanac_data.py:361-385
    #   "label": "Memorial Day Week, 26-30 May"
    #   "name": "Memorial Day week / week after options expiration"
    #   "seasonal_bias": "Mixed"
    #   "confidence": "Low-Medium"
    #   "bullets": [
    #       "Memorial Day week: Dow down 17 of last 29. Bearish lean.",
    #       "Day after Memorial Day: Dow down 8 of last 10. Recent trend bearish.",
    #       "Week after options expiration: S&P up 30 of 45, avg +0.40%. Mild bullish offset.",
    #       "Net: mixed / slight bearish lean.",
    #   ]
    #   "thesis": "Seasonality suggests caution in late May..."
    #
    # MONTHLY_STATS[5] at almanac_data.py:140-168
    #   "monthly_bias": "Mixed"
    #
    # SECTOR_WINDOWS at almanac_data.py:524-569:
    #   Technology (XLK): "seasonal LONG window (March-July)"
    #   Banking / Financials (XLF): "seasonal SHORT window (May-July)"
    # ---------------------------------------------------------------
    tmp_path = setup_integration
    prediction_date = date(2026, 5, 27)
    ctx = PipelineContext(prediction_date=prediction_date)
    config = {"artifacts": {"save_json": True, "save_md": True}}

    run_almanac(ctx, config)

    assert ctx.almanac is not None
    assert ctx.almanac.prediction_date == prediction_date
    assert ctx.almanac.monthly_bias == Bias.MIXED
    assert ctx.almanac.seasonal_bias == Bias.MIXED
    assert ctx.almanac.confidence == Confidence.LOW_MEDIUM

    tech_signal = next(s for s in ctx.almanac.sector_signals if "Technology" in s.sector)
    assert tech_signal.bias == Bias.BULLISH
    assert "seasonal LONG window (March-July)" in tech_signal.window

    banking_signal = next(s for s in ctx.almanac.sector_signals if "Banking" in s.sector)
    assert banking_signal.bias == Bias.BEARISH
    assert "seasonal SHORT window (May-July)" in banking_signal.window

    _verify_artifacts(
        tmp_path,
        week_str="W22",
        expected_json={
            "prediction_date": "2026-05-27",
            "monthly_bias": "Mixed",
            "seasonal_bias": "Mixed",
            "confidence": "Low-Medium",
        },
        expected_md_contains=[
            "MONTH: May 2026",
            "Memorial Day week: Dow down 17 of last 29",
            "Day after Memorial Day: Dow down 8 of last 10",
            "Week after options expiration: S&P up 30 of 45",
        ]
    )


def test_almanac_integration_week_2_early_june(setup_integration):
    # ---------------------------------------------------------------
    # WEEKLY_PATTERNS[(6, 1)] at almanac_data.py:386-415
    #   "label": "Early June Week, 2-6 June"
    #   "name": "Early June midterm-year weakness"
    #   "seasonal_bias": "Bearish"
    #   "confidence": "Medium"
    #   "bullets": [
    #       "No specific holiday pattern is active this week.",
    #       "Early June is transitional as summer doldrums begin.",
    #       "Volume tends to decline in early June as institutional activity slows.",
    #       "NFP on Friday 5 June is the dominant market event this week.",
    #   ]
    #   "thesis": "June 2026 is the worst month of the year in a midterm cycle..."
    #
    # MONTHLY_STATS[6] at almanac_data.py:169-197
    #   "monthly_bias": "Bearish"
    #
    # SECTOR_WINDOWS: Oil / Energy (XLE) at almanac_data.py:561-569
    #   "window": "seasonal SHORT begins in early June"
    # ---------------------------------------------------------------
    tmp_path = setup_integration
    prediction_date = date(2026, 6, 3)
    ctx = PipelineContext(prediction_date=prediction_date)
    config = {"artifacts": {"save_json": True, "save_md": True}}

    run_almanac(ctx, config)

    assert ctx.almanac is not None
    assert ctx.almanac.prediction_date == prediction_date
    assert ctx.almanac.monthly_bias == Bias.BEARISH
    assert ctx.almanac.seasonal_bias == Bias.BEARISH
    assert ctx.almanac.confidence == Confidence.MEDIUM

    oil_signal = next(s for s in ctx.almanac.sector_signals if "Oil" in s.sector)
    assert oil_signal.bias == Bias.BEARISH
    assert "seasonal SHORT begins in early June" in oil_signal.window

    _verify_artifacts(
        tmp_path,
        week_str="W23",
        expected_json={
            "prediction_date": "2026-06-03",
            "monthly_bias": "Bearish",
            "seasonal_bias": "Bearish",
            "confidence": "Medium",
        },
        expected_md_contains=[
            "MONTH: June 2026",
            "No specific holiday pattern is active this week.",
            "Early June is transitional as summer doldrums begin.",
            "Volume tends to decline in early June as institutional activity slows.",
            "NFP on Friday 5 June is the dominant market event this week.",
        ]
    )


def test_almanac_integration_week_3_mid_june(setup_integration):
    # ---------------------------------------------------------------
    # Stock Trader's Almanac 2026, p.87 (June 15-19)
    #   Seasonal bias: Bearish / Mixed. Confidence: Moderate.
    #   June is the weakest month of the year during a midterm cycle
    #   (Ranked #12 across DJIA, S&P 500, NASDAQ). Midterm avg: -1.9%
    #   DJIA, -2.1% S&P 500.
    #
    #   Key day-level events from the book:
    #     Mon 6/15: Monday of Triple-Witching Week, Dow down 15 of last 28
    #     Tue 6/16: Triple-Witching Week often up in bull markets /
    #               down in bears (p.108)
    #     Wed 6/17: FOMC Meeting scheduled
    #     Thu 6/18: June Triple-Witching Day mixed, but down 8 of last 10
    #     Fri 6/19: Juneteenth — Markets CLOSED
    #
    # → Encoded as WEEKLY_PATTERNS[(6, 3)] at almanac_data.py:416-435
    #   "seasonal_bias": "Bearish" (matches book)
    #   "confidence": "Medium"    (matches book "Moderate")
    #
    # MONTHLY_STATS[6] at almanac_data.py:169-197
    #   "monthly_bias": "Bearish" (matches book)
    # ---------------------------------------------------------------
    tmp_path = setup_integration
    prediction_date = date(2026, 6, 16)
    ctx = PipelineContext(prediction_date=prediction_date)
    config = {"artifacts": {"save_json": True, "save_md": True}}

    run_almanac(ctx, config)

    assert ctx.almanac is not None
    assert ctx.almanac.prediction_date == prediction_date
    assert ctx.almanac.monthly_bias == Bias.BEARISH
    assert ctx.almanac.seasonal_bias == Bias.BEARISH
    assert ctx.almanac.confidence == Confidence.MEDIUM
    assert ctx.almanac.weekly_pattern == "Mid-June weakness / Triple-Witching week"

    _verify_artifacts(
        tmp_path,
        week_str="W25",
        expected_json={
            "prediction_date": "2026-06-16",
            "monthly_bias": "Bearish",
            "seasonal_bias": "Bearish",
            "confidence": "Medium",
            "weekly_pattern": "Mid-June weakness / Triple-Witching week",
        },
        expected_md_contains=[
            "Almanac Agent Output",
            "MONTH: June 2026",
            "CYCLE CONTEXT:",
            "MONTHLY STATS:",
            "SPECIFIC WEEK PATTERN (Mid-June Week, 15-19 June):",
            "SECTOR SIGNALS:",
            "ALMANAC SEASONAL BIAS: Bearish.",
            "PATTERN CONFIDENCE: MEDIUM.",
            'ALMANAC THESIS: "Mid-June Triple-Witching week',
        ]
    )


def test_almanac_integration_week_4_late_june(setup_integration):
    # ---------------------------------------------------------------
    # Stock Trader's Almanac 2026, p.89 (June 22-26)
    #   Seasonal bias: Bearish. Confidence: Moderate.
    #   "Week After June Triple-Witching, Dow down 29 of last 35.
    #    Average loss since 1990 is 0.8%."
    #   June 23-26: No specific daily stats, but p.81 warns
    #   "Summer doldrums can begin in late June."
    #
    #   Monthly: June is #12 (dead last) in midterm cycle. p.87.
    #
    # ⚠ DISCREPANCY: WEEKLY_PATTERNS[(6, 4)] at almanac_data.py:436-456
    #   has "seasonal_bias": "Mixed" and "confidence": "Low-Medium",
    #   but the book says Bearish / Moderate.  This test is set to
    #   match the book (truth).  It will FAIL until almanac_data.py
    #   is fixed.  See also: the encoded "quarter-end positioning"
    #   narrative is not in the book for this week — the book focuses
    #   on the post-Triple-Witching downdraft.
    # ---------------------------------------------------------------
    tmp_path = setup_integration
    prediction_date = date(2026, 6, 24)
    ctx = PipelineContext(prediction_date=prediction_date)
    config = {"artifacts": {"save_json": True, "save_md": True}}

    run_almanac(ctx, config)

    assert ctx.almanac is not None
    assert ctx.almanac.prediction_date == prediction_date
    assert ctx.almanac.monthly_bias == Bias.BEARISH
    assert ctx.almanac.seasonal_bias == Bias.BEARISH
    assert ctx.almanac.confidence == Confidence.MEDIUM

    _verify_artifacts(
        tmp_path,
        week_str="W26",
        expected_json={
            "prediction_date": "2026-06-24",
            "monthly_bias": "Bearish",
            "seasonal_bias": "Bearish",
            "confidence": "Medium",
        },
        expected_md_contains=[
            "MONTH: June 2026",
            "Monday, June 22: Week after June Triple-Witching",
            "Dow down 29 of last 35",
            "Average loss for S&P 500 since 1990 during this week is -0.8%",
            "Summer doldrums can begin in late June",
        ]
    )


def test_almanac_integration_week_5_early_july(setup_integration):
    # ---------------------------------------------------------------
    # Stock Trader's Almanac 2026, p.97 & p.99 (July 6-10)
    #   Seasonal bias: Bullish / Mixed. Confidence: Moderate to Strong.
    #   July is the best month of Q3. In midterm years it ranks #3 for
    #   Dow (avg +1.6%) and #3 for S&P 500 (avg +1.3%). NASDAQ drops
    #   to #7 (avg -0.8%).
    #
    #   Specific day notes from the book:
    #     Mon 7/6: "Market subject to elevated volatility after July 4th"
    #     Wed 7/8: "Beware the Summer Rally hype — historically the
    #              weakest rally of all seasons" (p.76)
    #     Thu-Fri: No specific daily trends highlighted.
    #
    # → Encoded as WEEKLY_PATTERNS[(7, 1)] at almanac_data.py:477-496
    #   "seasonal_bias": "Bullish" (matches book, though book notes
    #     "/Mixed" qualifier and NASDAQ midterm weakness)
    #   "confidence": "Medium" (book says "Moderate to Strong";
    #     Confidence enum has no MEDIUM_HIGH value, so MEDIUM is closest)
    #
    # MONTHLY_STATS[7] at almanac_data.py:198-225
    #   "monthly_bias": "Mixed" (book says July is highly bullish
    #     overall; the "Mixed" may reflect midterm-year discounting)
    # ---------------------------------------------------------------
    tmp_path = setup_integration
    prediction_date = date(2026, 7, 7)
    ctx = PipelineContext(prediction_date=prediction_date)
    config = {"artifacts": {"save_json": True, "save_md": True}}

    run_almanac(ctx, config)

    assert ctx.almanac is not None
    assert ctx.almanac.prediction_date == prediction_date
    assert ctx.almanac.monthly_bias == Bias.MIXED
    assert ctx.almanac.seasonal_bias == Bias.MIXED
    assert ctx.almanac.confidence == Confidence.MEDIUM

    _verify_artifacts(
        tmp_path,
        week_str="W28",
        expected_json={
            "prediction_date": "2026-07-07",
            "monthly_bias": "Mixed",
            "seasonal_bias": "Mixed",
            "confidence": "Medium",
        },
        expected_md_contains=[
            "MONTH: July 2026",
            "Elevated volatility after Independence Day",
            "July is the best month of Q3",
            "ranks #3 for Dow",
            "(+1.3%) in midterm years",
            "NASDAQ midterm-year July ranks only #7",
        ]
    )
