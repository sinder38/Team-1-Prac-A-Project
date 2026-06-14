from backend.agents.technical.technical_agent import TechnicalAgent, EmaSnapshot
from backend.agents.schemas import Bias, Confidence


# ==========================================================
# TEST 1
# Verify that a strong bullish EMA structure returns:
# Bias = Bullish
# Confidence = High
#
# Condition:
# Price > EMA8 > EMA21
# ==========================================================
def test_assess_trend_bullish_high_confidence():
    agent = TechnicalAgent()
    snap = EmaSnapshot(price=100, ema_fast=95, ema_slow=90)

    bias, confidence = agent._assess_trend(snap)

    assert bias == Bias.BULLISH
    assert confidence == Confidence.HIGH


# ==========================================================
# TEST 2
# Verify that a strong bearish EMA structure returns:
# Bias = Bearish
# Confidence = High
#
# Condition:
# Price < EMA8 < EMA21
# ==========================================================
def test_assess_trend_bearish_high_confidence():
    agent = TechnicalAgent()
    snap = EmaSnapshot(price=90, ema_fast=95, ema_slow=100)

    bias, confidence = agent._assess_trend(snap)

    assert bias == Bias.BEARISH
    assert confidence == Confidence.HIGH


# ==========================================================
# TEST 3
# Verify that mixed EMA signals return:
# Bias = Neutral
# Confidence = Low
#
# Condition:
# Price > EMA8 but EMA8 < EMA21
# ==========================================================
def test_assess_trend_neutral_low_confidence():
    agent = TechnicalAgent()
    snap = EmaSnapshot(price=100, ema_fast=90, ema_slow=95)

    bias, confidence = agent._assess_trend(snap)

    assert bias == Bias.NEUTRAL
    assert confidence == Confidence.LOW


# ==========================================================
# TEST 4
# Verify that a weak bullish trend returns:
# Bias = Bullish
# Confidence = Medium
#
# EMA gap is small, therefore confidence should
# not be High.
# ==========================================================
def test_assess_trend_bullish_medium_confidence():
    agent = TechnicalAgent()
    snap = EmaSnapshot(price=100, ema_fast=99.9, ema_slow=99.7)

    bias, confidence = agent._assess_trend(snap)

    assert bias == Bias.BULLISH
    assert confidence == Confidence.MEDIUM


# ==========================================================
# TEST 5
# Verify that a weak bearish trend returns:
# Bias = Bearish
# Confidence = Medium
#
# EMA gap is small, therefore confidence should
# not be High.
# ==========================================================
def test_assess_trend_bearish_medium_confidence():
    agent = TechnicalAgent()
    snap = EmaSnapshot(price=99.8, ema_fast=99.9, ema_slow=100)

    bias, confidence = agent._assess_trend(snap)

    assert bias == Bias.BEARISH
    assert confidence == Confidence.MEDIUM


# ==========================================================
# TEST 6
# Verify EMA Zone 1 classification.
#
# Condition:
# Price > EMA8 > EMA21
#
# Expected:
# Zone 1 (Bullish)
# ==========================================================
def test_ema_zone_bullish():
    agent = TechnicalAgent()

    zone_id, zone_label, description = agent._ema_zone(100, 95, 90)

    assert zone_id == 1
    assert zone_label == Bias.BULLISH.value
    assert "price above both EMAs" in description


# ==========================================================
# TEST 7
# Verify EMA Zone 4 classification.
#
# Condition:
# Price < EMA8 < EMA21
#
# Expected:
# Zone 4 (Bearish)
# ==========================================================
def test_ema_zone_bearish():
    agent = TechnicalAgent()

    zone_id, zone_label, description = agent._ema_zone(90, 95, 100)

    assert zone_id == 4
    assert zone_label == Bias.BEARISH.value
    assert "price below both EMAs" in description


# ==========================================================
# TEST 8
# Verify compressed EMA condition.
#
# Condition:
# Price = EMA8 = EMA21
#
# Expected:
# Zone 0 (Neutral)
# ==========================================================
def test_ema_zone_compressed_neutral():
    agent = TechnicalAgent()

    zone_id, zone_label, description = agent._ema_zone(100, 100, 100)

    assert zone_id == 0
    assert zone_label == Bias.NEUTRAL.value
    assert "EMAs compressed" in description
