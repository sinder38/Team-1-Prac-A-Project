import json
import pytest
from datetime import date

from agents.pipeline.context import PipelineContext
from agents.pipeline.stages import run_almanac
from agents.schemas import Bias, Confidence


@pytest.fixture
def setup_integration(tmp_path, monkeypatch):
    """Fixture to patch output directories to tmp_path so tests do not touch actual outputs."""
    monkeypatch.setattr("agents.pipeline.stages.REPO_ROOT", tmp_path)
    monkeypatch.setattr("agents.io.DATA_ROOT", tmp_path / "outputs")
    return tmp_path


def _verify_artifacts(tmp_path, week_str, expected_json, expected_md_contains):
    """Helper to verify both JSON and Markdown artifacts on disk to keep tests DRY."""
    # 1. Verify JSON file saving and fields
    json_path = tmp_path / "outputs" / "almanac" / f"{week_str}.json"
    assert json_path.exists(), f"JSON output file was not created at {json_path}"
    with open(json_path, "r", encoding="utf-8") as f:
        saved_data = json.load(f)
    for key, value in expected_json.items():
        assert saved_data[key] == value, f"Key '{key}' mismatch in JSON: expected {value}, got {saved_data[key]}"

    # 2. Verify Markdown file saving and substrings
    md_path = tmp_path / "data" / "almanac" / f"almanac_agent_{week_str}.md"
    assert md_path.exists(), f"Markdown output file was not created at {md_path}"
    md_content = md_path.read_text(encoding="utf-8")
    for substring in expected_md_contains:
        assert substring in md_content, f"Expected substring '{substring}' not found in Markdown content"


def test_almanac_integration_fallback(setup_integration):
    """Test fallback scenario: a date without an encoded weekly pattern (e.g. 2026-12-15)."""
    tmp_path = setup_integration
    prediction_date = date(2026, 12, 15)
    ctx = PipelineContext(prediction_date=prediction_date)
    config = {"artifacts": {"save_json": True, "save_md": True}}

    run_almanac(ctx, config)

    # Context checks
    assert ctx.almanac is not None
    assert ctx.almanac.prediction_date == prediction_date
    assert ctx.almanac.monthly_bias == Bias.BULLISH
    assert ctx.almanac.seasonal_bias == Bias.BULLISH
    assert ctx.almanac.confidence == Confidence.LOW

    # Disk checks
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
    """Week 1 of 5: Memorial Day Week (May Week 4 - 2026-05-27)."""
    tmp_path = setup_integration
    prediction_date = date(2026, 5, 27)
    ctx = PipelineContext(prediction_date=prediction_date)
    config = {"artifacts": {"save_json": True, "save_md": True}}

    run_almanac(ctx, config)

    # Context checks
    assert ctx.almanac is not None
    assert ctx.almanac.prediction_date == prediction_date
    assert ctx.almanac.monthly_bias == Bias.MIXED
    assert ctx.almanac.seasonal_bias == Bias.MIXED
    assert ctx.almanac.confidence == Confidence.LOW_MEDIUM

    # Sector checks
    tech_signal = next(s for s in ctx.almanac.sector_signals if "Technology" in s.sector)
    assert tech_signal.bias == Bias.BULLISH
    assert "seasonal LONG window (March-July)" in tech_signal.window

    banking_signal = next(s for s in ctx.almanac.sector_signals if "Banking" in s.sector)
    assert banking_signal.bias == Bias.BEARISH
    assert "seasonal SHORT window (May-July)" in banking_signal.window

    # Disk checks
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
    """Week 2 of 5: Early June Week (June Week 1 - 2026-06-03)."""
    tmp_path = setup_integration
    prediction_date = date(2026, 6, 3)
    ctx = PipelineContext(prediction_date=prediction_date)
    config = {"artifacts": {"save_json": True, "save_md": True}}

    run_almanac(ctx, config)

    # Context checks
    assert ctx.almanac is not None
    assert ctx.almanac.prediction_date == prediction_date
    assert ctx.almanac.monthly_bias == Bias.BEARISH
    assert ctx.almanac.seasonal_bias == Bias.BEARISH
    assert ctx.almanac.confidence == Confidence.MEDIUM

    # Sector check
    oil_signal = next(s for s in ctx.almanac.sector_signals if "Oil" in s.sector)
    assert oil_signal.bias == Bias.BEARISH
    assert "seasonal SHORT begins in early June" in oil_signal.window

    # Disk checks
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
    """Week 3 of 5: Mid-June Week (June Week 3 - 2026-06-16)."""
    tmp_path = setup_integration
    prediction_date = date(2026, 6, 16)
    ctx = PipelineContext(prediction_date=prediction_date)
    config = {"artifacts": {"save_json": True, "save_md": True}}

    run_almanac(ctx, config)

    # Context checks
    assert ctx.almanac is not None
    assert ctx.almanac.prediction_date == prediction_date
    assert ctx.almanac.monthly_bias == Bias.BEARISH
    assert ctx.almanac.seasonal_bias == Bias.BEARISH
    assert ctx.almanac.confidence == Confidence.MEDIUM
    assert ctx.almanac.weekly_pattern == "Mid-June weakness / CPI follow-through week"

    # Disk checks
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
    """Week 4 of 5: Late June Week (June Week 4 - 2026-06-24)."""
    tmp_path = setup_integration
    prediction_date = date(2026, 6, 24)
    ctx = PipelineContext(prediction_date=prediction_date)
    config = {"artifacts": {"save_json": True, "save_md": True}}

    run_almanac(ctx, config)

    # Context checks
    assert ctx.almanac is not None
    assert ctx.almanac.prediction_date == prediction_date
    assert ctx.almanac.monthly_bias == Bias.BEARISH
    assert ctx.almanac.seasonal_bias == Bias.MIXED
    assert ctx.almanac.confidence == Confidence.LOW_MEDIUM

    # Disk checks
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
    """Week 5 of 5: Early July Week (July Week 1 - 2026-07-07)."""
    tmp_path = setup_integration
    prediction_date = date(2026, 7, 7)
    ctx = PipelineContext(prediction_date=prediction_date)
    config = {"artifacts": {"save_json": True, "save_md": True}}

    run_almanac(ctx, config)

    # Context checks
    assert ctx.almanac is not None
    assert ctx.almanac.prediction_date == prediction_date
    assert ctx.almanac.monthly_bias == Bias.MIXED
    assert ctx.almanac.seasonal_bias == Bias.BULLISH
    assert ctx.almanac.confidence == Confidence.MEDIUM

    # Disk checks
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
