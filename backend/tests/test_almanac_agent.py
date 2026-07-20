import json
import pytest
from datetime import date
from pathlib import Path

from agents.almanac.almanac_agent import AlmanacAgent
from agents.schemas import AlmanacOutput, Bias, Confidence
from agents.pipeline.context import PipelineContext
from agents.pipeline.stages import run_almanac


class _FakeConfig:
    """Works as both dict-access (.get) and dot-access (.artifacts.save_json).

    Needed because local stages.py uses config.get("artifacts", {}) while the CI
    branch uses config.artifacts.save_json (PipelineConfig).  This class supports
    both at once so the same test file passes in both environments.
    """
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, _FakeConfig(**v) if isinstance(v, dict) else v)
    def get(self, key, default=None):
        return getattr(self, key, default)


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
    # 2026-06-16 maps to June, Week 3 (6, 3), which is encoded in WEEKLY_PATTERNS.
    #
    # Stock Trader's Almanac 2026, p.87 (June 15-19):
    #   Midterm-year June is dead last (#12) across DJIA, S&P 500, NASDAQ.
    #   Monday of Triple-Witching Week — Dow down 15 of last 28.
    #   Wednesday: FOMC. Thursday: Triple-witching day down 8 of last 10.
    #   Friday: Juneteenth — market CLOSED.
    #
    agent = AlmanacAgent()
    output = agent.lookup_seasonal_data(date(2026, 6, 16))

    assert isinstance(output, AlmanacOutput)
    assert output.prediction_date == date(2026, 6, 16)
    assert output.monthly_bias == Bias.BEARISH
    assert output.seasonal_bias == Bias.BEARISH
    assert output.confidence == Confidence.MEDIUM
    assert output.weekly_pattern == "Mid-June weakness / CPI follow-through week"
    assert len(output.sector_signals) > 0
    assert "Almanac setup stays cautious" in output.thesis


def test_lookup_seasonal_data_fallback():
    # 2026-12-15 is a Tuesday in December, Week 3 (12, 3), which is NOT in WEEKLY_PATTERNS.
    # Falls back to MONTHLY_STATS[12] monthly_bias "Bullish" at confidence "Low".
    agent = AlmanacAgent()
    output = agent.lookup_seasonal_data(date(2026, 12, 15))

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


REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_ALMANAC_DIR = REPO_ROOT / "data" / "almanac"


@pytest.fixture
def setup_integration(tmp_path, monkeypatch):
    """Fixture to patch output directories to tmp_path so tests do not touch actual outputs."""
    monkeypatch.setattr("agents.pipeline.stages.REPO_ROOT", tmp_path)
    try:
        monkeypatch.setattr("agents.pipeline.stages.DATA_DIR", tmp_path / "data")
    except AttributeError:
        pass
    monkeypatch.setattr("agents.io.DATA_ROOT", tmp_path / "outputs")
    return tmp_path


def _load_reference_almanac(week_str: str) -> str | None:
    """Load the hand-authored team almanac file for this ISO week, if one exists."""
    path = REFERENCE_ALMANAC_DIR / f"almanac_agent_{week_str}.md"
    return path.read_text(encoding="utf-8") if path.exists() else None


def _assert_phrases_from_almanac_source(
    generated_md: str,
    week_str: str,
    phrases: list[str],
    *,
    citation: str,
) -> None:
    """Cross-check agent output against the team's almanac reference notes.

    Each phrase must appear in the generated Markdown. When a reference file exists
    under data/almanac/, the same phrase must also appear there so reviewers can
    trace assertions back to the original almanac research without re-parsing code.
    """
    reference = _load_reference_almanac(week_str)
    for phrase in phrases:
        assert phrase in generated_md, (
            f"Agent output missing almanac phrase ({citation}): {phrase!r}"
        )
        if reference is not None:
            assert phrase in reference, (
                f"Phrase not in reference almanac_agent_{week_str}.md "
                f"({citation}): {phrase!r}"
            )


def _verify_artifacts(tmp_path, week_str, expected_json, expected_md_contains, *, almanac_source=None):
    """Helper to verify both JSON and Markdown artifacts on disk to keep tests DRY."""
    json_path = tmp_path / "outputs" / "almanac" / f"{week_str}.json"
    assert json_path.exists(), f"JSON output file was not created at {json_path}"
    with open(json_path, "r", encoding="utf-8") as f:
        saved_data = json.load(f)
    for key, value in expected_json.items():
        assert saved_data[key] == value, f"Key '{key}' mismatch in JSON: expected {value}, got {saved_data[key]}"

    md_path = tmp_path / "data" / "almanac" / f"almanac_agent_{week_str}.md"
    assert md_path.exists(), f"Markdown output file was not created at {md_path}"
    md_content = md_path.read_text(encoding="utf-8")
    for substring in expected_md_contains:
        assert substring in md_content, f"Expected substring '{substring}' not found in Markdown content"

    if almanac_source:
        _assert_phrases_from_almanac_source(
            md_content,
            week_str,
            almanac_source["phrases"],
            citation=almanac_source["citation"],
        )


def test_almanac_integration_fallback(setup_integration):
    """Test fallback scenario: a date without an encoded weekly pattern (e.g. 2026-12-15)."""
    tmp_path = setup_integration
    prediction_date = date(2026, 12, 15)
    ctx = PipelineContext(prediction_date=prediction_date)
    config = _FakeConfig(artifacts={"save_json": True, "save_md": True})

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
    """Week 1 of 5: Memorial Day Week (May Week 4 — 2026-05-27, ISO W22).

    Almanac source: data/almanac/almanac_agent_W22.md
    Stock Trader's Almanac 2026, pp. 65-66 (May Vital Statistics), p. 94 (Sector Seasonality),
    pp. 10-11 (2026 Outlook).
    """
    tmp_path = setup_integration
    prediction_date = date(2026, 5, 27)
    ctx = PipelineContext(prediction_date=prediction_date)
    config = _FakeConfig(artifacts={"save_json": True, "save_md": True})

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
        ],
        almanac_source={
            "citation": "data/almanac/almanac_agent_W22.md; STA 2026 pp. 65-66, p. 94, pp. 10-11",
            "phrases": [
                # SPECIFIC WEEK PATTERN — Memorial Day week (W22 reference lines 13-16)
                "Memorial Day week: Dow down 17 of last 29",
                "Dow down 8 of last 10",
                "S&P up 30 of 45",
                # MONTHLY STATS — May vital statistics (W22 reference lines 7-10)
                "ranks #8 of 12 months",
                "61% of the time",
                "Avg +0.3% normally",
                "Midterm year May",
                # SECTOR SIGNALS — sector seasonality table (W22 reference lines 19-22)
                "seasonal LONG",
                "seasonal SHORT",
            ],
        },
    )


def test_almanac_integration_week_2_early_june(setup_integration):
    """Week 2 of 5: Early June Week (June Week 1 — 2026-06-03, ISO W23).

    Almanac source: data/almanac/almanac_agent_W23.md
    Encoded from W22 next-week context (June ranks #12 midterm, S&P -2.1%) and
    Stock Trader's Almanac June seasonal summaries.
    """
    tmp_path = setup_integration
    prediction_date = date(2026, 6, 3)
    ctx = PipelineContext(prediction_date=prediction_date)
    config = _FakeConfig(artifacts={"save_json": True, "save_md": True})

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
        ],
        almanac_source={
            "citation": "data/almanac/almanac_agent_W23.md; W22 next-week context lines 28-32",
            "phrases": [
                # MONTHLY STATS — June midterm-year context (W23 reference lines 7-10)
                "Dead last in the midterm-year pattern for S&P 500",
                "Avg -2.1% for S&P 500",
                # SPECIFIC WEEK PATTERN (W23 reference lines 13-17)
                "No specific holiday pattern is active this week.",
                "Early June is transitional as summer doldrums begin.",
                "NFP on Friday 5 June is the dominant market event this week.",
                # ALMANAC THESIS (W23 reference line 28)
                "June 2026 is the worst month of the year in a midterm cycle",
                # SECTOR — new Oil/Energy short from W22 next-week context line 31
                "seasonal SHORT begins in early June",
            ],
        },
    )


def test_almanac_integration_week_3_mid_june(setup_integration):
    """Week 3 of 5: Mid-June Week (June Week 3 — 2026-06-16, ISO W25).

    Almanac source: data/almanac/almanac_agent_W25.md

    Stock Trader's Almanac 2026, p.87 (June 15-19):
      June is the weakest month of the year during a midterm election cycle
      (Ranked #12 across DJIA, S&P 500, NASDAQ). Midterm avg: -1.9% DJIA,
      -2.1% S&P 500.
      Mon 6/15: Monday of Triple-Witching Week — Dow down 15 of last 28.
      Tue 6/16: Triple-Witching Week often up in bull markets / down in bears (p.108).
      Wed 6/17: FOMC Meeting scheduled.
      Thu 6/18: June Triple-Witching Day mixed, but down 8 of last 10.
      Fri 6/19: Juneteenth — Markets CLOSED.
    """
    tmp_path = setup_integration
    prediction_date = date(2026, 6, 16)
    ctx = PipelineContext(prediction_date=prediction_date)
    config = _FakeConfig(artifacts={"save_json": True, "save_md": True})

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
        ],
        almanac_source={
            "citation": "data/almanac/almanac_agent_W25.md; STA 2026 p.87, p.108",
            "phrases": [
                # SPECIFIC WEEK PATTERN (W25 reference lines 13-17)
                "June midterm-year weakness remains the main seasonal background.",
                "The market is still inside the Q2-Q3 Weak Spot",
                "A holiday-shortened week around Juneteenth can reduce liquidity",
                # ALMANAC THESIS (W25 reference line 28)
                "Seasonality is still a headwind in mid-June because June is the weakest month",
                "the broader Almanac setup stays cautious",
            ],
        },
    )


def test_almanac_integration_week_4_late_june(setup_integration):
    """Week 4 of 5: Late June Week (June Week 4 — 2026-06-24, ISO W26).

    Stock Trader's Almanac 2026, p.89 (June 22-26):
      "Week After June Triple-Witching, Dow down 29 of last 35.
       Average loss since 1990 is 0.8%."
      June 23-26: No specific daily stats, but p.81 warns
      "Summer doldrums can begin in late June."
      Monthly: June is #12 (dead last) in midterm cycle. p.87.

    No hand-authored data/almanac/almanac_agent_W26.md yet —
    encoded from WEEKLY_PATTERNS[(6, 4)] bullets.
    """
    tmp_path = setup_integration
    prediction_date = date(2026, 6, 24)
    ctx = PipelineContext(prediction_date=prediction_date)
    config = _FakeConfig(artifacts={"save_json": True, "save_md": True})

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
            "Dow down 29 of last 35",
        ],
        almanac_source={
            "citation": "WEEKLY_PATTERNS[(6,4)]; STA 2026 p.89, p.81, p.87",
            "phrases": [
                "Late June can see quarter-end positioning and rebalancing flows.",
                "Midterm-year June remains weak even if short-term bounces appear.",
                "Summer trading volume may start to thin, which can exaggerate moves.",
                "Dow down 29 of last 35",
            ],
        },
    )


def test_almanac_integration_week_5_early_july(setup_integration):
    """Week 5 of 5: Early July Week (July Week 1 — 2026-07-07, ISO W28).

    Almanac source: data/almanac/almanac_agent_W28.md

    Stock Trader's Almanac 2026, p.97 & p.99 (July 6-10):
      July is the best month of Q3. Midterm years: ranks #3 for Dow (+1.6%),
      #3 for S&P 500 (+1.3%). NASDAQ drops to #7 (-0.8%).
      Mon 7/6: "Market subject to elevated volatility after July 4th."
      Wed 7/8: "Beware the Summer Rally hype — historically the weakest
      rally of all seasons" (p.76).
    """
    tmp_path = setup_integration
    prediction_date = date(2026, 7, 7)
    ctx = PipelineContext(prediction_date=prediction_date)
    config = _FakeConfig(artifacts={"save_json": True, "save_md": True})

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
        ],
        almanac_source={
            "citation": "WEEKLY_PATTERNS[(7,1)]; STA 2026 p.97, p.99, p.76",
            "phrases": [
                "Early July is often one of the more constructive parts of the summer calendar.",
                "New-month and second-half inflows can support index performance.",
                "The midterm-year Weak Spot still argues against overconfidence.",
            ],
        },
    )
