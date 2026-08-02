"""Compare manual W22/W23 technical reports with TechnicalAgent auto-fetch output.

Manual baselines come from:
  - data/technical/technical_agent_W22.md
  - data/technical/technnical_agent_W23.md

Each case runs TechnicalAgent against the historical prediction date (yfinance),
then checks that automatically fetched prices, EMA structure, and bias/confidence
line up with the manually completed week.
"""

from __future__ import annotations

from datetime import date
from typing import NamedTuple

import pytest

from core.schemas import Bias, Confidence
from agents.technical.technical_agent import TechnicalAgent


class ManualCase(NamedTuple):
    week: str
    prediction_date: date
    symbol: str
    last_close: float
    ema_8: float
    ema_21: float
    # Schema-level expectation after mapping free-text manual labels
    # (e.g. Neutral-Bullish / Neutral-Bearish -> Neutral or Bullish).
    expected_bias: Bias
    expected_confidence: Confidence
    price_above_ema8: bool
    ema8_above_ema21: bool
    # W22 chart estimates were precise enough to compare EMAs directly.
    # W23 estimates reused stale levels; only price + structure are compared.
    compare_emas: bool
    close_atol: float = 1.0
    ema_atol: float = 2.0


MANUAL_CASES = [
    ManualCase(
        week="W22",
        prediction_date=date(2026, 5, 29),
        symbol="SPX",
        last_close=7580.06,
        ema_8=7505.06,
        ema_21=7389.24,
        expected_bias=Bias.BULLISH,
        expected_confidence=Confidence.HIGH,
        price_above_ema8=True,
        ema8_above_ema21=True,
        compare_emas=True,
    ),
    ManualCase(
        week="W22",
        prediction_date=date(2026, 5, 29),
        symbol="NDX",
        last_close=30333.18,
        ema_8=29810.55,
        ema_21=28982.86,
        expected_bias=Bias.BULLISH,
        expected_confidence=Confidence.HIGH,
        price_above_ema8=True,
        ema8_above_ema21=True,
        compare_emas=True,
    ),
    # Manual label was Neutral-Bullish / Medium; schema maps Price > 8 > 21 to Bullish / High.
    ManualCase(
        week="W22",
        prediction_date=date(2026, 5, 29),
        symbol="IWM",
        last_close=290.43,
        ema_8=287.24,
        ema_21=282.38,
        expected_bias=Bias.BULLISH,
        expected_confidence=Confidence.HIGH,
        price_above_ema8=True,
        ema8_above_ema21=True,
        compare_emas=True,
        close_atol=1.0,
        ema_atol=1.0,
    ),
    ManualCase(
        week="W23",
        prediction_date=date(2026, 6, 5),
        symbol="SPX",
        last_close=7383.74,
        ema_8=7445.30,
        ema_21=7389.24,
        expected_bias=Bias.NEUTRAL,
        expected_confidence=Confidence.LOW,
        price_above_ema8=False,
        ema8_above_ema21=True,
        compare_emas=False,
    ),
    # Manual label was Neutral-Bearish; schema has Neutral only.
    ManualCase(
        week="W23",
        prediction_date=date(2026, 6, 5),
        symbol="NDX",
        last_close=28957.60,
        ema_8=29427.32,
        ema_21=28982.86,
        expected_bias=Bias.NEUTRAL,
        expected_confidence=Confidence.LOW,
        price_above_ema8=False,
        ema8_above_ema21=True,
        compare_emas=False,
    ),
    ManualCase(
        week="W23",
        prediction_date=date(2026, 6, 5),
        symbol="IWM",
        last_close=281.65,
        ema_8=284.55,
        ema_21=282.38,
        expected_bias=Bias.NEUTRAL,
        expected_confidence=Confidence.LOW,
        price_above_ema8=False,
        ema8_above_ema21=True,
        compare_emas=False,
        close_atol=1.0,
    ),
]


@pytest.fixture(scope="module")
def auto_outputs_by_date():
    """Fetch each unique prediction date once via TechnicalAgent."""
    agent = TechnicalAgent()
    outputs = {}
    for case in MANUAL_CASES:
        if case.prediction_date in outputs:
            continue
        try:
            outputs[case.prediction_date] = agent.run(case.prediction_date)
        except Exception as exc:  # noqa: BLE001 — network / data vendor failures
            pytest.skip(f"Automatic fetch failed for {case.prediction_date}: {exc}")
    return outputs


@pytest.mark.parametrize("case", MANUAL_CASES, ids=lambda c: f"{c.week}-{c.symbol}")
def test_auto_fetch_matches_manual_week(case: ManualCase, auto_outputs_by_date):
    output = auto_outputs_by_date[case.prediction_date]
    auto = output.instruments[case.symbol]

    assert auto.last_close == pytest.approx(
        case.last_close, abs=case.close_atol
    ), f"{case.week} {case.symbol} last_close diverged from manual report"

    if case.compare_emas:
        assert auto.ema_8 == pytest.approx(
            case.ema_8, abs=case.ema_atol
        ), f"{case.week} {case.symbol} ema_8 diverged from manual report"
        assert auto.ema_21 == pytest.approx(
            case.ema_21, abs=case.ema_atol
        ), f"{case.week} {case.symbol} ema_21 diverged from manual report"

    assert (auto.last_close > auto.ema_8) is case.price_above_ema8, (
        f"{case.week} {case.symbol} price vs 8 EMA structure differs from manual"
    )
    assert (auto.ema_8 > auto.ema_21) is case.ema8_above_ema21, (
        f"{case.week} {case.symbol} 8 vs 21 EMA structure differs from manual"
    )

    assert auto.trend_bias == case.expected_bias, (
        f"{case.week} {case.symbol} auto bias {auto.trend_bias} "
        f"!= expected {case.expected_bias}"
    )
    assert auto.confidence == case.expected_confidence, (
        f"{case.week} {case.symbol} auto confidence {auto.confidence} "
        f"!= expected {case.expected_confidence}"
    )
