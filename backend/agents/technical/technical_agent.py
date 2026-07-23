"""
Technical Agent — EMA-based technical analysis via yfinance.
  SPX -> ^GSPC   NDX -> ^NDX   IWM -> IWM

Usage:
    python agents/technical/technical_agent.py 2026-06-16
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Final, Literal, NamedTuple, TypeAlias, cast

import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.base import BaseAgent
from core.schemas import Bias, Confidence, InstrumentTechnical, TechnicalOutput

Symbol: TypeAlias = Literal["SPX", "NDX", "IWM"]

INSTRUMENTS: Final[list[Symbol]] = ["SPX", "NDX", "IWM"]
TICKERS: Final[dict[Symbol, str]] = {"SPX": "^GSPC", "NDX": "^NDX", "IWM": "IWM"}
LABELS: Final[dict[Symbol, str]] = {
    "SPX": "S&P 500 (SPX), Daily Chart",
    "NDX": "Nasdaq 100 (NDX), Daily Chart",
    "IWM": "Russell 2000 (IWM), Daily Chart",
}

EMA_FAST_SPAN: Final[int] = 8
EMA_SLOW_SPAN: Final[int] = 21
LOOKBACK_DAYS: Final[int] = 20
EXTENDED_LOOKBACK_DAYS: Final[int] = 90
SWING_WINDOW: Final[int] = 5
HISTORY_DAYS: Final[int] = (
    150  # calendar days; gives ~90 trading sessions after weekends/holidays
)
EMA_GAP_CONFIDENCE_PCT: Final[float] = 0.5
PRICE_EMA_DISTANCE_CONFIDENCE_PCT: Final[float] = 0.2


class EmaSnapshot(NamedTuple):
    price: float
    ema_fast: float
    ema_slow: float


def _fmt(v: float) -> str:
    return f"{v:,.0f}" if v >= 1000 else f"{v:,.2f}"


def _pct(part: float, whole: float) -> float:
    return 0.0 if whole == 0 else abs(part) / whole * 100.0


class TechnicalAgent(BaseAgent):
    agent_type = "technical"

    # Frames cached during run() so render_md() doesn't need to re-fetch.
    _frames: dict[Symbol, pd.DataFrame]

    def _fetch_ohlcv(self, symbol: Symbol, prediction_date: date) -> pd.DataFrame:
        """Pulls daily OHLCV trimmed to prediction_date — no lookahead."""
        ticker = TICKERS[symbol]
        raw = yf.download(
            ticker,
            start=(prediction_date - timedelta(days=HISTORY_DAYS)).isoformat(),
            end=(prediction_date + timedelta(days=1)).isoformat(),
            progress=False,
            auto_adjust=True,
        )
        if raw is None or raw.empty:
            raise ValueError(f"No data for {symbol} ({ticker})")

        df = raw
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.sort_index()
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df = df.dropna(subset=["Close", "High", "Low"])
        df = df.loc[df.index <= pd.Timestamp(prediction_date)]

        if df.empty:
            raise ValueError(f"No data on or before {prediction_date} for {symbol}")
        return df

    def _compute_emas(self, closes: pd.Series) -> EmaSnapshot:
        """adjust=False matches most charting platforms."""
        return EmaSnapshot(
            price=float(closes.iloc[-1]),
            ema_fast=float(
                closes.ewm(span=EMA_FAST_SPAN, adjust=False).mean().iloc[-1]
            ),
            ema_slow=float(
                closes.ewm(span=EMA_SLOW_SPAN, adjust=False).mean().iloc[-1]
            ),
        )

    def _swing_levels(self, df: pd.DataFrame) -> tuple[float, float, float, float]:
        """Returns (support, resistance, secondary_support, secondary_resistance).
        Primary window = recent LOOKBACK_DAYS; secondary = EXTENDED_LOOKBACK_DAYS."""

        def hi_lo(n: int) -> tuple[float, float]:
            w = df.tail(n)
            lo = float(
                w["Low"].rolling(SWING_WINDOW, min_periods=1).min().to_numpy().min()
            )
            hi = float(
                w["High"].rolling(SWING_WINDOW, min_periods=1).max().to_numpy().max()
            )
            return lo, hi

        sup, res = hi_lo(LOOKBACK_DAYS)
        sup2, res2 = hi_lo(min(len(df), EXTENDED_LOOKBACK_DAYS))
        return sup, res, sup2, res2

    def _assess_trend(self, s: EmaSnapshot) -> tuple[Bias, Confidence]:
        if s.price > s.ema_fast > s.ema_slow:
            bias = Bias.BULLISH
        elif s.price < s.ema_fast < s.ema_slow:
            bias = Bias.BEARISH
        else:
            return Bias.NEUTRAL, Confidence.LOW

        strong = (
            _pct(s.ema_fast - s.ema_slow, s.price) > EMA_GAP_CONFIDENCE_PCT
            and _pct(s.price - s.ema_fast, s.price) > PRICE_EMA_DISTANCE_CONFIDENCE_PCT
        )
        return bias, Confidence.HIGH if strong else Confidence.MEDIUM

    def fetch_instrument(
        self, symbol: Symbol, prediction_date: date
    ) -> InstrumentTechnical:
        df = self._fetch_ohlcv(symbol, prediction_date)
        self._frames[symbol] = df

        snap = self._compute_emas(cast(pd.Series, df["Close"]))
        sup, res, *_ = self._swing_levels(df)
        bias, confidence = self._assess_trend(snap)

        return InstrumentTechnical(
            last_close=round(snap.price, 2),
            ema_8=round(snap.ema_fast, 2),
            ema_21=round(snap.ema_slow, 2),
            trend_bias=bias,
            key_support=round(sup, 2),
            key_resistance=round(res, 2),
            confidence=confidence,
        )

    def run(
        self,
        prediction_date: date,
        instruments: list[Symbol] = INSTRUMENTS,
        **kwargs,
    ) -> TechnicalOutput:
        horizon_days = int(kwargs.get("horizon_days", 7))
        self._frames = {}
        results: dict[str, InstrumentTechnical] = {}
        for symbol in instruments:
            results[symbol] = self.fetch_instrument(symbol, prediction_date)
        return TechnicalOutput(prediction_date=prediction_date, instruments=results, horizon_days=horizon_days,)

    def _ema_zone(self, p: float, fast: float, slow: float) -> tuple[int, str, str]:
        neutral = Bias.NEUTRAL.value
        if p > fast > slow:
            return 1, Bias.BULLISH.value, "price above both EMAs"
        if p < fast < slow:
            return 4, Bias.BEARISH.value, "price below both EMAs"
        if fast > slow:
            return 2, f"{neutral}-{Bias.BULLISH.value}", "8 EMA above 21 EMA"
        if fast < slow:
            return 3, f"{neutral}-{Bias.BEARISH.value}", "8 EMA below 21 EMA"
        return 0, neutral, "EMAs compressed"

    def _invalidation(self, bias: Bias, sup: float, res: float) -> str:
        if bias == Bias.BULLISH:
            return f"Close below {_fmt(sup)}."
        if bias == Bias.BEARISH:
            return f"Close above {_fmt(res)}."
        return (
            f"Close below {_fmt(sup)} shifts to {Bias.BEARISH.value}; "
            f"close above {_fmt(res)} shifts to {Bias.BULLISH.value}."
        )

    def _render_block(
        self, symbol: Symbol, inst: InstrumentTechnical, bar_date: date, horizon_days: int = 7
    ) -> list[str]:
        p, e8, e21 = inst.last_close, inst.ema_8, inst.ema_21
        sup, res, sup2, res2 = self._swing_levels(self._frames[symbol])
        zid, zlabel, zdesc = self._ema_zone(p, e8, e21)
        watch = (
            "WATCH THIS WEEK"
            if horizon_days <= 7
            else f"WATCH NEXT {horizon_days} DAYS"
        )

        return [
            f"INSTRUMENT: {LABELS[symbol]}",
            f"LAST CLOSE: {_fmt(p)} ({bar_date.strftime('%a %d %b %Y')})",
            "",
            "8 EMA vs PRICE:",
            f" - Price is {'ABOVE' if p > e8 else 'BELOW'} the 8 EMA.",
            f" - 8 EMA at ~{_fmt(e8)}; gap {_fmt(abs(p - e8))} pts.",
            "",
            "8 EMA vs 21 EMA:",
            f" - 8 EMA is {'ABOVE' if e8 > e21 else 'BELOW'} 21 EMA.",
            f" - 21 EMA at ~{_fmt(e21)}; gap {_fmt(abs(e8 - e21))} pts.",
            f" - EMA condition: Zone {zid} ({zlabel}) — {zdesc}.",
            "",
            "TRENDLINE:",
            f" - Swing support over the last {LOOKBACK_DAYS} sessions.",
            f" - Trendline range: {_fmt(inst.key_support)}–{_fmt(e21)}.",
            f" - Price is {'above' if p > inst.key_support else 'below'} support.",
            "",
            "KEY LEVELS:",
            f" - Resistance 1: {_fmt(res)}.",
            f" - Resistance 2: {_fmt(res2)}.",
            f" - Support 1: {_fmt(sup)}.",
            f" - Support 2: {_fmt(sup2)}.",
            "",
            # TODO: cross-index breadth (% above 200-day MA, relative strength)
            "BREADTH NOTE:",
            f" - Breadth data not available for {symbol} in this scaffold.",
            "",
            f"TECHNICAL BIAS: {inst.trend_bias.value}.",
            f"CONFIDENCE: {inst.confidence.value}.",
            f"INVALIDATION: {self._invalidation(inst.trend_bias, inst.key_support, inst.key_resistance)}",
            f"{watch}: Watch {_fmt(res)} resistance and {_fmt(sup)} support.",
        ]

    def render_md(self, output: TechnicalOutput, prediction_date: date) -> str:
        horizon_days = getattr(output, "horizon_days", 7)
        title = (
            f"Technical Agent Output — Week of {prediction_date.day} {prediction_date.strftime('%B %Y')}"
            if horizon_days <= 7
            else f"Technical Agent Output — Next {horizon_days} days from {prediction_date.day} {prediction_date.strftime('%B %Y')}"
        )

        lines = [
            f"{title }",
            "",
            "Quick note: The 8 EMA is a short-term average price line. The 21 EMA is a "
            "longer-term average. When price sits above both and the 8 is above the 21, "
            "the trend is usually up.",
            "",
            "---",
            "",
        ]
        symbols: list[Symbol] = [
            cast(Symbol, s) for s in INSTRUMENTS if s in output.instruments
        ]
        for i, symbol in enumerate(symbols):
            df = self._frames[symbol]
            last_ts = pd.to_datetime(str(df.index[-1]))
            if pd.isna(last_ts):
                raise ValueError(f"No valid bar date for {symbol}")
            bar_date = cast(date, last_ts.date())
            lines.extend(
                self._render_block(symbol, output.instruments[symbol], bar_date, horizon_days)
            )
            if i < len(symbols) - 1:
                lines.extend(["", "---", ""])
        return "\n".join(lines)

    @staticmethod
    def _week_md_filename(prediction_date: date) -> str:
        return f"technical_agent_W{prediction_date.isocalendar().week:02d}.md"


if __name__ == "__main__":
    from core.io import FileSaver, week_stem

    prediction_date = (
        date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    )
    agent = TechnicalAgent()
    output = agent.run(prediction_date)

    FileSaver.for_agent(agent.agent_type).save(
        agent.render_json(output, prediction_date), f"{week_stem(prediction_date)}.json"
    )

    md_dir = Path(__file__).resolve().parents[3] / "data" / "technical"
    md_dir.mkdir(parents=True, exist_ok=True)
    md_path = md_dir / TechnicalAgent._week_md_filename(prediction_date)
    md_path.write_text(agent.render_md(output, prediction_date), encoding="utf-8")
    print(f"Saved JSON to backend/data/outputs/technical/ and MD to {md_path}")
