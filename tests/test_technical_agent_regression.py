import pytest

from backend.agents.technical.technical_agent import TechnicalAgent, EmaSnapshot
from backend.agents.schemas import Bias, Confidence


# ==========================================================
# HISTORICAL REGRESSION DATA
# Values are taken from manually completed W22 and W23
# Technical Agent reports.
# ==========================================================
HISTORICAL_CASES = [
    # week, symbol, price, ema8, ema21, expected_bias, expected_confidence
    ("W22", "SPX", 7580.06, 7505.06, 7389.24, Bias.BULLISH, Confidence.HIGH),
    ("W22", "NDX", 30333.18, 29810.55, 28982.86, Bias.BULLISH, Confidence.HIGH),

    # IWM was manually described as Neutral-Bullish / Medium,
    # but current schema maps this EMA structure to Bullish / High.
    ("W22", "IWM", 290.43, 287.24, 282.38, Bias.BULLISH, Confidence.HIGH),

    # W23 sharp reversal cases.
    ("W23", "SPX", 7383.74, 7445.30, 7389.24, Bias.NEUTRAL, Confidence.LOW),
    ("W23", "NDX", 28957.60, 29427.32, 28982.86, Bias.NEUTRAL, Confidence.LOW),
    ("W23", "IWM", 281.65, 284.55, 282.38, Bias.NEUTRAL, Confidence.LOW),
]


# ==========================================================
# TEST 1
# Regression test using previous manually completed weeks.
#
# It checks that the Technical Agent still classifies
# historical EMA setups consistently.
# ==========================================================
@pytest.mark.parametrize(
    "week,symbol,price,ema8,ema21,expected_bias,expected_confidence",
    HISTORICAL_CASES,
)
def test_historical_technical_bias_regression(
    week,
    symbol,
    price,
    ema8,
    ema21,
    expected_bias,
    expected_confidence,
):
    agent = TechnicalAgent()
    snap = EmaSnapshot(price=price, ema_fast=ema8, ema_slow=ema21)

    bias, confidence = agent._assess_trend(snap)

    assert bias == expected_bias, f"{week} {symbol} bias changed"
    assert confidence == expected_confidence, f"{week} {symbol} confidence changed"


# ==========================================================
# TEST 2
# Historical W22 bullish EMA zone check.
#
# W22 SPX and NDX had:
# Price > EMA8 > EMA21
# Expected zone = 1 Bullish
# ==========================================================
@pytest.mark.parametrize(
    "symbol,price,ema8,ema21",
    [
        ("SPX", 7580.06, 7505.06, 7389.24),
        ("NDX", 30333.18, 29810.55, 28982.86),
    ],
)
def test_w22_historical_bullish_ema_zone(symbol, price, ema8, ema21):
    agent = TechnicalAgent()

    zone_id, zone_label, description = agent._ema_zone(price, ema8, ema21)

    assert zone_id == 1, f"W22 {symbol} EMA zone changed"
    assert zone_label == Bias.BULLISH.value
    assert "price above both EMAs" in description


# ==========================================================
# TEST 3
# Historical W23 reversal check.
#
# W23 reports showed price fell below EMA8,
# meaning bullish trend weakened.
# Current implementation should classify these as Neutral.
# ==========================================================
@pytest.mark.parametrize(
    "symbol,price,ema8,ema21",
    [
        ("SPX", 7383.74, 7445.30, 7389.24),
        ("NDX", 28957.60, 29427.32, 28982.86),
        ("IWM", 281.65, 284.55, 282.38),
    ],
)
def test_w23_historical_reversal_is_not_bullish(symbol, price, ema8, ema21):
    agent = TechnicalAgent()
    snap = EmaSnapshot(price=price, ema_fast=ema8, ema_slow=ema21)

    bias, confidence = agent._assess_trend(snap)

    assert bias != Bias.BULLISH, f"W23 {symbol} should not remain bullish"
    assert confidence == Confidence.LOW
