import pytest
from datetime import date
from pathlib import Path

from agents.almanac.almanac_agent import AlmanacAgent
from agents.schemas import AlmanacOutput, Bias, Confidence


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
    # 2026-06-16 is Tuesday
    start, end = AlmanacAgent._week_bounds(date(2026, 6, 16))
    assert start == date(2026, 6, 15)  # Monday
    assert end == date(2026, 6, 19)    # Friday


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
    # 2026-06-16 maps to June, Week 3 (6, 3), which is encoded in WEEKLY_PATTERNS
    agent = AlmanacAgent()
    output = agent.lookup_seasonal_data(date(2026, 6, 16))

    assert isinstance(output, AlmanacOutput)
    assert output.prediction_date == date(2026, 6, 16)
    assert output.monthly_bias == Bias.BEARISH  # June monthly bias is Bearish
    assert output.seasonal_bias == Bias.BEARISH  # (6, 3) pattern seasonal bias is Bearish
    assert output.confidence == Confidence.MEDIUM
    assert output.weekly_pattern == "Mid-June weakness / CPI follow-through week"
    assert len(output.sector_signals) > 0
    assert "Almanac setup stays cautious" in output.thesis


def test_lookup_seasonal_data_fallback():
    # 2026-12-15 is a Tuesday in December, Week 3 (12, 3), which is NOT in WEEKLY_PATTERNS
    agent = AlmanacAgent()
    output = agent.lookup_seasonal_data(date(2026, 12, 15))

    assert isinstance(output, AlmanacOutput)
    assert output.prediction_date == date(2026, 12, 15)
    assert output.monthly_bias == Bias.BULLISH  # Dec monthly bias is Bullish
    assert output.seasonal_bias == Bias.BULLISH  # Falls back to Dec monthly bias
    assert output.confidence == Confidence.LOW   # Fallback confidence is Low
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
