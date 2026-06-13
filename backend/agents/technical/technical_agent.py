"""
Technical Agent — fetches price data and computes EMA-based technical analysis.

Data source: yfinance
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

from agents.base import BaseAgent
from agents.schemas import Bias, Confidence, InstrumentTechnical, TechnicalOutput

# Types

Symbol: TypeAlias = Literal["SPX", "NDX", "IWM"]
"""Supported index/ETF symbols tracked by this agent."""


class EmaSnapshot(NamedTuple):
    """Latest price and exponential moving averages derived from daily closes."""

    price: float
    ema_fast: float
    ema_slow: float


class SwingLevels(NamedTuple):
    """Rolling swing high/low used as key support and resistance."""

    support: float
    resistance: float
    secondary_support: float
    secondary_resistance: float


class EmaZone(NamedTuple):
    """Human-readable EMA alignment zone for markdown rendering."""

    zone_id: int
    label: str
    description: str


class TrendAssessment(NamedTuple):
    """Combined trend bias and confidence for one instrument."""

    bias: Bias
    confidence: Confidence


# Constants — instruments & data source

INSTRUMENTS: Final[list[Symbol]] = ["SPX", "NDX", "IWM"]

TICKERS: Final[dict[Symbol, str]] = {
    "SPX": "^GSPC",
    "NDX": "^NDX",
    "IWM": "IWM",
}

LABELS: Final[dict[Symbol, str]] = {
    "SPX": "S&P 500 (SPX), Daily Chart",
    "NDX": "Nasdaq 100 (NDX), Daily Chart",
    "IWM": "Russell 2000 (IWM), Daily Chart",
}

# Constants — lookback & indicator parameters

EMA_FAST_SPAN: Final[int] = 8
EMA_SLOW_SPAN: Final[int] = 21
LOOKBACK_DAYS: Final[int] = 20
EXTENDED_LOOKBACK_DAYS: Final[int] = 90
SWING_WINDOW: Final[int] = 5
SWING_MIN_PERIODS: Final[int] = 1
HISTORY_DAYS: Final[int] = 90

EMA_ADJUST: Final[bool] = False
PERCENT_SCALE: Final[float] = 100.0

PRICE_ROUND_DIGITS: Final[int] = 2

# Confidence scoring: minimum EMA gap and price-to-fast-EMA distance (as % of price).
EMA_GAP_CONFIDENCE_PCT: Final[float] = 0.5
PRICE_EMA8_DISTANCE_CONFIDENCE_PCT: Final[float] = 0.2

# Markdown rendering tokens.
APPROX_PREFIX: Final[str] = "~"

# Constants — yfinance fetch

YF_END_DAY_BUFFER: Final[int] = 1
YF_AUTO_ADJUST: Final[bool] = True
YF_SHOW_PROGRESS: Final[bool] = False
OHLCV_REQUIRED_COLUMNS: Final[tuple[str, ...]] = ("Close", "High", "Low")

# Constants — EMA zone IDs (markdown template)

ZONE_NEUTRAL: Final[int] = 0
ZONE_BULLISH: Final[int] = 1
ZONE_NEUTRAL_BULLISH: Final[int] = 2
ZONE_NEUTRAL_BEARISH: Final[int] = 3
ZONE_BEARISH: Final[int] = 4

# Composite zone labels built from schema Bias string values.
NEUTRAL_BULLISH_LABEL: Final[str] = f"{Bias.NEUTRAL.value}-{Bias.BULLISH.value}"
NEUTRAL_BEARISH_LABEL: Final[str] = f"{Bias.NEUTRAL.value}-{Bias.BEARISH.value}"

# Format large index levels without decimals; keep decimals for smaller prices (e.g. IWM).
LARGE_PRICE_THRESHOLD: Final[float] = 1000.0

QUICK_NOTE: Final[str] = (
    "Quick note: The 8 EMA is a short-term average price line. "
    "The 21 EMA is a longer-term average. When price sits above both "
    "and the 8 is above the 21, the trend is usually up."
)


class TechnicalAgent(BaseAgent):
    agent_type = "technical"

    # Data fetching & normalization

    def _fetch_ohlcv(self, symbol: Symbol, prediction_date: date) -> pd.DataFrame:
        """
        Download daily OHLCV from yfinance and trim to prediction_date.

        No future bars are included so indicators never use lookahead data.
        """
        ticker = TICKERS[symbol]
        start = prediction_date - timedelta(days=HISTORY_DAYS)
        raw = yf.download(
            ticker,
            start=start.isoformat(),
            end=(prediction_date + timedelta(days=YF_END_DAY_BUFFER)).isoformat(),
            progress=YF_SHOW_PROGRESS,
            auto_adjust=YF_AUTO_ADJUST,
        )
        if raw is None or raw.empty:
            raise ValueError(f"No price data returned for {symbol} ({ticker})")

        df: pd.DataFrame = raw
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.sort_index()
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df = df.dropna(subset=list(OHLCV_REQUIRED_COLUMNS))
        df = df.loc[df.index <= pd.Timestamp(prediction_date)]
        if df.empty:
            raise ValueError(
                f"No price data on or before {prediction_date} for {symbol} ({ticker})"
            )
        return df

    def _compute_emas(self, closes: pd.Series) -> EmaSnapshot:
        """Compute fast/slow EMAs; adjust=False matches common chart platforms."""
        ema_fast = float(
            closes.ewm(span=EMA_FAST_SPAN, adjust=EMA_ADJUST).mean().iloc[-1]
        )
        ema_slow = float(
            closes.ewm(span=EMA_SLOW_SPAN, adjust=EMA_ADJUST).mean().iloc[-1]
        )
        price = float(closes.iloc[-1])
        return EmaSnapshot(price=price, ema_fast=ema_fast, ema_slow=ema_slow)

    def _swing_from_window(
        self, df: pd.DataFrame, window_days: int
    ) -> tuple[float, float]:
        """Lowest low and highest high over window_days with rolling smooth."""
        recent = df.tail(window_days)
        support = float(
            recent["Low"]
            .rolling(SWING_WINDOW, min_periods=SWING_MIN_PERIODS)
            .min()
            .min()  # type: ignore[arg-type]
        )
        resistance = float(
            recent["High"]
            .rolling(SWING_WINDOW, min_periods=SWING_MIN_PERIODS)
            .max()
            .max()  # type: ignore[arg-type]
        )
        return support, resistance

    def _compute_swing_levels(self, df: pd.DataFrame) -> SwingLevels:
        """
        Derive primary and secondary support/resistance from fetched OHLCV data.

        Primary levels use the short LOOKBACK_DAYS window (recent swing structure).
        Secondary levels use the longer EXTENDED_LOOKBACK_DAYS window so Resistance 2
        and Support 2 reflect actual historical highs/lows rather than fixed offsets.
        """
        support, resistance = self._swing_from_window(df, LOOKBACK_DAYS)
        extended_window = min(len(df), EXTENDED_LOOKBACK_DAYS)
        secondary_support, secondary_resistance = self._swing_from_window(
            df, extended_window
        )
        return SwingLevels(
            support=support,
            resistance=resistance,
            secondary_support=secondary_support,
            secondary_resistance=secondary_resistance,
        )

    def _assess_trend(self, snapshot: EmaSnapshot) -> TrendAssessment:
        """
        Classify trend bias from price vs EMA stack, then score confidence.

        Bias rules:
          - Bullish: price > fast EMA > slow EMA
          - Bearish: price < fast EMA < slow EMA
          - Neutral: any other alignment (mixed stack)

        Confidence rises when EMAs are separated and price is clearly away from
        the fast EMA; neutral bias always maps to low confidence.
        """
        price, ema_fast, ema_slow = snapshot

        if price > ema_fast > ema_slow:
            bias = Bias.BULLISH
        elif price < ema_fast < ema_slow:
            bias = Bias.BEARISH
        else:
            bias = Bias.NEUTRAL

        if bias == Bias.NEUTRAL:
            confidence = Confidence.LOW
        elif (
            self._pct_of(ema_fast - ema_slow, price) > EMA_GAP_CONFIDENCE_PCT
            and self._pct_of(price - ema_fast, price)
            > PRICE_EMA8_DISTANCE_CONFIDENCE_PCT
        ):
            confidence = Confidence.HIGH
        else:
            confidence = Confidence.MEDIUM

        return TrendAssessment(bias=bias, confidence=confidence)

    def _round_price(self, value: float) -> float:
        """Round monetary values to a consistent number of decimal places."""
        return round(value, PRICE_ROUND_DIGITS)

    @staticmethod
    def _pct_of(part: float, whole: float) -> float:
        """Return |part| as a percentage of whole using PERCENT_SCALE."""
        if whole == 0:
            return 0.0
        return abs(part) / whole * PERCENT_SCALE

    # Public API

    def fetch_instrument(
        self, symbol: Symbol, prediction_date: date
    ) -> InstrumentTechnical:
        """Fetch price data and compute EMAs for a single instrument."""
        df = self._fetch_ohlcv(symbol, prediction_date)

        closes = cast(pd.Series, df["Close"])
        snapshot = self._compute_emas(closes)
        levels = self._compute_swing_levels(df)
        assessment = self._assess_trend(snapshot)

        return InstrumentTechnical(
            last_close=self._round_price(snapshot.price),
            ema_8=self._round_price(snapshot.ema_fast),
            ema_21=self._round_price(snapshot.ema_slow),
            trend_bias=assessment.bias,
            key_support=self._round_price(levels.support),
            key_resistance=self._round_price(levels.resistance),
            confidence=assessment.confidence,
        )

    def run(
        self, prediction_date: date, instruments: list[Symbol] = INSTRUMENTS, **kwargs
    ) -> TechnicalOutput:
        results: dict[str, InstrumentTechnical] = {}
        for symbol in instruments:
            results[symbol] = self.fetch_instrument(symbol, prediction_date)
        return TechnicalOutput(prediction_date=prediction_date, instruments=results)

    # Markdown rendering

    def _resolve_ema_zone(
        self, price: float, ema_fast: float, ema_slow: float
    ) -> EmaZone:
        """Map price/EMA alignment to a numbered zone for the markdown template."""
        if price > ema_fast > ema_slow:
            return EmaZone(ZONE_BULLISH, Bias.BULLISH.value, "price above both EMAs")
        if price < ema_fast < ema_slow:
            return EmaZone(ZONE_BEARISH, Bias.BEARISH.value, "price below both EMAs")
        if ema_fast > ema_slow:
            return EmaZone(
                ZONE_NEUTRAL_BULLISH,
                NEUTRAL_BULLISH_LABEL,
                "8 EMA above 21 EMA",
            )
        if ema_fast < ema_slow:
            return EmaZone(
                ZONE_NEUTRAL_BEARISH,
                NEUTRAL_BEARISH_LABEL,
                "8 EMA below 21 EMA",
            )
        return EmaZone(ZONE_NEUTRAL, Bias.NEUTRAL.value, "EMAs compressed")

    @staticmethod
    def _format_week_title(prediction_date: date) -> str:
        """Human-readable week title matching team markdown convention."""
        return f"{prediction_date.day} {prediction_date.strftime('%B %Y')}"

    @staticmethod
    def _week_md_filename(prediction_date: date) -> str:
        """Filename pattern expected by agent-checks CI (technical_agent_W*.md)."""
        week = prediction_date.isocalendar().week
        return f"technical_agent_W{week:02d}.md"

    @staticmethod
    def _format_price(value: float) -> str:
        """Format index levels: whole numbers above threshold, decimals below."""
        if value >= LARGE_PRICE_THRESHOLD:
            return f"{value:,.0f}"
        return f"{value:,.2f}"

    def _approx_price(self, value: float) -> str:
        return f"{APPROX_PREFIX}{self._format_price(value)}"

    def _gap_points(self, a: float, b: float) -> str:
        return self._format_price(abs(a - b))

    def _invalidation_text(self, bias: Bias, support: float, resistance: float) -> str:
        """One-line invalidation rule keyed off the current trend bias."""
        fmt = self._format_price
        if bias == Bias.BULLISH:
            return f"Close below {fmt(support)}."
        if bias == Bias.BEARISH:
            return f"Close above {fmt(resistance)}."
        return (
            f"Close below {fmt(support)} shifts to {Bias.BEARISH.value}; "
            f"close above {fmt(resistance)} shifts to {Bias.BULLISH.value}."
        )

    def _render_breadth_note(self, symbol: Symbol) -> list[str]:
        # TODO: add cross-index breadth (% above 200-day MA, relative strength).
        return [
            "BREADTH NOTE:",
            f" - Breadth data not available for {symbol} in this scaffold.",
        ]

    def _render_block(
        self,
        symbol: Symbol,
        inst: InstrumentTechnical,
        bar_date: date,
        levels: SwingLevels,
    ) -> list[str]:
        p, e8, e21 = inst.last_close, inst.ema_8, inst.ema_21
        above8, above21 = p > e8, e8 > e21
        zone = self._resolve_ema_zone(p, e8, e21)
        fmt = self._format_price

        above_support = p > inst.key_support
        return [
            f"INSTRUMENT: {LABELS[symbol]}",
            f"LAST CLOSE: {fmt(p)} ({bar_date.strftime('%a %d %b %Y')})",
            "",
            "8 EMA vs PRICE:",
            f" - Price is {'ABOVE' if above8 else 'BELOW'} the 8 EMA.",
            f" - 8 EMA at {self._approx_price(e8)}; gap {self._gap_points(p, e8)} pts.",
            "",
            "8 EMA vs 21 EMA:",
            f" - 8 EMA is {'ABOVE' if above21 else 'BELOW'} 21 EMA.",
            f" - 21 EMA at {self._approx_price(e21)}; gap {self._gap_points(e8, e21)} pts.",
            f" - EMA condition: Zone {zone.zone_id} ({zone.label}) — {zone.description}.",
            "",
            "TRENDLINE:",
            f" - Swing support over the last {LOOKBACK_DAYS} sessions.",
            f" - Trendline range: {fmt(inst.key_support)}–{fmt(e21)}.",
            f" - Price is {'above' if above_support else 'below'} support.",
            "",
            "KEY LEVELS:",
            f" - Resistance 1: {fmt(inst.key_resistance)}.",
            f" - Resistance 2: {fmt(levels.secondary_resistance)}.",
            f" - Support 1: {fmt(inst.key_support)}.",
            f" - Support 2: {fmt(levels.secondary_support)}.",
            "",
            *self._render_breadth_note(symbol),
            "",
            f"TECHNICAL BIAS: {inst.trend_bias.value}.",
            f"CONFIDENCE: {inst.confidence.value}.",
            f"INVALIDATION: {self._invalidation_text(inst.trend_bias, inst.key_support, inst.key_resistance)}",
            f"WATCH THIS WEEK: Watch {fmt(inst.key_resistance)} resistance and {fmt(inst.key_support)} support.",
        ]

    def render_md(self, output: TechnicalOutput, prediction_date: date) -> str:
        """Render TechnicalOutput to MD matching data/formats/technical_agent.md"""
        lines = [
            f"Technical Agent Output — Week of {self._format_week_title(prediction_date)}",
            "",
            QUICK_NOTE,
            "",
            "---",
            "",
        ]
        symbols: list[Symbol] = [
            cast(Symbol, s) for s in output.instruments if s in INSTRUMENTS
        ]
        for i, symbol in enumerate(symbols):
            # Re-fetch OHLCV to recover the actual last bar date and extended swing levels.
            df = self._fetch_ohlcv(symbol, prediction_date)
            last_ts = pd.to_datetime(str(df.index[-1]))
            if pd.isna(last_ts):
                raise ValueError(f"No valid bar date for {symbol}")
            bar_date = cast(date, last_ts.date())
            levels = self._compute_swing_levels(df)
            lines.extend(
                self._render_block(symbol, output.instruments[symbol], bar_date, levels)
            )
            if i < len(symbols) - 1:
                lines.extend(["", "---", ""])
        return "\n".join(lines)


def _technical_md_dir() -> Path:
    """Directory for technical agent MD files validated by CI."""
    return Path(__file__).resolve().parent.parent.parent.parent / "data" / "technical"


if __name__ == "__main__":
    from agents.io import FileSaver, week_stem

    prediction_date = (
        date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    )
    agent = TechnicalAgent()
    output = agent.run(prediction_date)

    stem = week_stem(prediction_date)
    saver = FileSaver.for_agent(agent.agent_type)
    saver.save(agent.render_json(output, prediction_date), f"{stem}.json")

    md_dir = _technical_md_dir()
    md_dir.mkdir(parents=True, exist_ok=True)
    md_path = md_dir / TechnicalAgent._week_md_filename(prediction_date)
    md_path.write_text(agent.render_md(output, prediction_date), encoding="utf-8")
    print(f"Saved JSON to backend/data/outputs/technical/ and MD to {md_path}")
