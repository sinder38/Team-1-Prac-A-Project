import json
import pytest
from datetime import date
from pathlib import Path
from types import SimpleNamespace

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
    # Source: WEEKLY_PATTERNS[(6, 3)] at almanac_data.py
    #   "name": "Mid-June weakness / CPI follow-through week"
    #   "seasonal_bias": "Bearish"
    #   "confidence": "Medium"
    #
    # Source: MONTHLY_STATS[6] at almanac_data.py
    #   "monthly_bias": "Bearish"
    #
    assert isinstance(output, AlmanacOutput)
    assert output.prediction_date == date(2026, 6, 16)
    assert output.monthly_bias == Bias.BEARISH
    assert output.seasonal_bias == Bias.BEARISH
    assert output.confidence == Confidence.MEDIUM
    assert output.weekly_pattern == "Mid-June weakness / CPI follow-through week"
    assert len(output.sector_signals) > 0
    assert "Almanac setup stays cautious" in output.thesis


def test_lookup_seasonal_data_fallback():
    agent = AlmanacAgent()
    output = agent.lookup_seasonal_data(date(2026, 12, 15))
    #
    # Source: MONTHLY_STATS[12] at almanac_data.py
    #   "monthly_bias": "Bullish"
    #
    # No WEEKLY_PATTERNS entry for (12, 3) — falls back to monthly bias.
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
    tmp_path = setup_integration
    prediction_date = date(2026, 12, 15)
    ctx = PipelineContext(prediction_date=prediction_date)
    config = SimpleNamespace(artifacts=SimpleNamespace(save_json=True, save_md=True))

    run_almanac(ctx, config)  # type: ignore[reportArgumentType]

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
    tmp_path = setup_integration
    prediction_date = date(2026, 5, 27)
    ctx = PipelineContext(prediction_date=prediction_date)
    config = SimpleNamespace(artifacts=SimpleNamespace(save_json=True, save_md=True))

    run_almanac(ctx, config)  # type: ignore[reportArgumentType]

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
    tmp_path = setup_integration
    prediction_date = date(2026, 6, 3)
    ctx = PipelineContext(prediction_date=prediction_date)
    config = SimpleNamespace(artifacts=SimpleNamespace(save_json=True, save_md=True))

    run_almanac(ctx, config)  # type: ignore[reportArgumentType]

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
    tmp_path = setup_integration
    prediction_date = date(2026, 6, 16)
    ctx = PipelineContext(prediction_date=prediction_date)
    config = SimpleNamespace(artifacts=SimpleNamespace(save_json=True, save_md=True))

    run_almanac(ctx, config)  # type: ignore[reportArgumentType]

    assert ctx.almanac is not None
    assert ctx.almanac.prediction_date == prediction_date
    assert ctx.almanac.monthly_bias == Bias.BEARISH
    assert ctx.almanac.seasonal_bias == Bias.BEARISH
    assert ctx.almanac.confidence == Confidence.MEDIUM
    assert ctx.almanac.weekly_pattern == "Mid-June weakness / CPI follow-through week"

    _verify_artifacts(
        tmp_path,
        week_str="W25",
        expected_json={
            "prediction_date": "2026-06-16",
            "monthly_bias": "Bearish",
            "seasonal_bias": "Bearish",
            "confidence": "Medium",
            "weekly_pattern": "Mid-June weakness / CPI follow-through week",
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
            'ALMANAC THESIS: "Seasonality is still a headwind in mid-June',
        ]
    )


def test_almanac_integration_week_4_late_june(setup_integration):
    tmp_path = setup_integration
    prediction_date = date(2026, 6, 24)
    ctx = PipelineContext(prediction_date=prediction_date)
    config = SimpleNamespace(artifacts=SimpleNamespace(save_json=True, save_md=True))

    run_almanac(ctx, config)  # type: ignore[reportArgumentType]

    assert ctx.almanac is not None
    assert ctx.almanac.prediction_date == prediction_date
    assert ctx.almanac.monthly_bias == Bias.BEARISH
    assert ctx.almanac.seasonal_bias == Bias.MIXED
    assert ctx.almanac.confidence == Confidence.LOW_MEDIUM

    _verify_artifacts(
        tmp_path,
        week_str="W26",
        expected_json={
            "prediction_date": "2026-06-24",
            "monthly_bias": "Bearish",
            "seasonal_bias": "Mixed",
            "confidence": "Low-Medium",
        },
        expected_md_contains=[
            "MONTH: June 2026",
            "Late June can see quarter-end positioning and rebalancing flows.",
            "Midterm-year June remains weak even if short-term bounces appear.",
            "Summer trading volume may start to thin, which can exaggerate moves.",
        ]
    )


def test_almanac_integration_week_5_early_july(setup_integration):
    tmp_path = setup_integration
    prediction_date = date(2026, 7, 7)
    ctx = PipelineContext(prediction_date=prediction_date)
    config = SimpleNamespace(artifacts=SimpleNamespace(save_json=True, save_md=True))

    run_almanac(ctx, config)  # type: ignore[reportArgumentType]

    assert ctx.almanac is not None
    assert ctx.almanac.prediction_date == prediction_date
    assert ctx.almanac.monthly_bias == Bias.MIXED
    assert ctx.almanac.seasonal_bias == Bias.BULLISH
    assert ctx.almanac.confidence == Confidence.MEDIUM

    _verify_artifacts(
        tmp_path,
        week_str="W28",
        expected_json={
            "prediction_date": "2026-07-07",
            "monthly_bias": "Mixed",
            "seasonal_bias": "Bullish",
            "confidence": "Medium",
        },
        expected_md_contains=[
            "MONTH: July 2026",
            "Early July is often one of the more constructive parts of the summer calendar.",
            "New-month and second-half inflows can support index performance.",
            "The midterm-year Weak Spot still argues against overconfidence.",
        ]
    )
