"""
Technical Agent — fetches price data and computes EMA-based technical analysis.

Data source: yfinance
  SPX -> ^GSPC   NDX -> ^NDX   IWM -> IWM

Usage:
    python agents/technical/technical_agent.py 2026-06-16
"""
from datetime import date, timedelta
from pathlib import Path
import sys

import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base import BaseAgent
from agents.schemas import TechnicalOutput, InstrumentTechnical, Bias, Confidence

INSTRUMENTS = ["SPX", "NDX", "IWM"]

TICKERS = {"SPX": "^GSPC", "NDX": "^NDX", "IWM": "IWM"}
LABELS = {
    "SPX": "S&P 500 (SPX), Daily Chart",
    "NDX": "Nasdaq 100 (NDX), Daily Chart",
    "IWM": "Russell 2000 (IWM), Daily Chart",
}
LOOKBACK, SWING, HISTORY = 20, 5, 90


class TechnicalAgent(BaseAgent):
    agent_type = "technical"

    def _fetch_ohlcv(self, symbol: str, prediction_date: date) -> pd.DataFrame:
        ticker = TICKERS[symbol]
        df = yf.download(
            ticker,
            start=(prediction_date - timedelta(days=HISTORY)).isoformat(),
            end=(prediction_date + timedelta(days=1)).isoformat(),
            progress=False,
            auto_adjust=True,
        )
        if df.empty:
            raise ValueError(f"No price data returned for {symbol} ({ticker})")
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.sort_index()
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df = df.dropna(subset=["Close", "High", "Low"])
        df = df[df.index <= pd.Timestamp(prediction_date)]
        if df.empty:
            raise ValueError(f"No price data on or before {prediction_date} for {symbol} ({ticker})")
        return df

    def fetch_instrument(self, symbol: str, prediction_date: date) -> InstrumentTechnical:
        """Fetch price data and compute EMAs for a single instrument."""
        df = self._fetch_ohlcv(symbol, prediction_date)
        closes = df["Close"]
        ema_8 = closes.ewm(span=8, adjust=False).mean().iloc[-1]
        ema_21 = closes.ewm(span=21, adjust=False).mean().iloc[-1]
        price = float(closes.iloc[-1])

        recent = df.tail(LOOKBACK)
        key_support = float(recent["Low"].rolling(SWING, min_periods=1).min().min())
        key_resistance = float(recent["High"].rolling(SWING, min_periods=1).max().max())

        if price > ema_8 > ema_21:
            trend_bias = Bias.BULLISH
        elif price < ema_8 < ema_21:
            trend_bias = Bias.BEARISH
        else:
            trend_bias = Bias.NEUTRAL

        if trend_bias == Bias.NEUTRAL:
            confidence = Confidence.LOW
        elif abs(ema_8 - ema_21) / price * 100 > 0.5 and abs(price - ema_8) / price * 100 > 0.2:
            confidence = Confidence.HIGH
        else:
            confidence = Confidence.MEDIUM

        return InstrumentTechnical(
            last_close=round(price, 2),
            ema_8=round(float(ema_8), 2),
            ema_21=round(float(ema_21), 2),
            trend_bias=trend_bias,
            key_support=round(key_support, 2),
            key_resistance=round(key_resistance, 2),
            confidence=confidence,
        )

    def run(self, prediction_date: date, instruments: list[str] = INSTRUMENTS, **kwargs) -> TechnicalOutput:
        results = {}
        for symbol in instruments:
            results[symbol] = self.fetch_instrument(symbol, prediction_date)
        return TechnicalOutput(prediction_date=prediction_date, instruments=results)

    def _render_block(self, symbol: str, inst: InstrumentTechnical, bar_date: date) -> list[str]:
        p, e8, e21 = inst.last_close, inst.ema_8, inst.ema_21
        above8, above21 = p > e8, e8 > e21

        if p > e8 > e21:
            zone = (1, "Bullish", "both rising, price above both")
        elif p < e8 < e21:
            zone = (4, "Bearish", "both falling, price below both")
        elif e8 > e21:
            zone = (2, "Neutral-Bullish", "8 above 21 but price not fully aligned")
        elif e8 < e21:
            zone = (3, "Neutral-Bearish", "8 below 21 but price not fully aligned")
        else:
            zone = (0, "Neutral", "EMAs compressed")

        fmt = lambda v: f"{v:,.0f}" if v >= 1000 else f"{v:,.2f}"
        bias_text = {
            Bias.BULLISH: "Bullish — price above both EMAs with bullish stack.",
            Bias.BEARISH: "Bearish — price below both EMAs with bearish stack.",
            Bias.NEUTRAL: "Neutral — EMA structure mixed; no clean trend stack.",
        }[inst.trend_bias]
        invalidation = {
            Bias.BULLISH: f"Close below {fmt(inst.key_support)} (20-day swing support).",
            Bias.BEARISH: f"Close above {fmt(inst.key_resistance)} (20-day swing resistance).",
            Bias.NEUTRAL: (
                f"Close below {fmt(inst.key_support)} shifts to Bearish; "
                f"close above {fmt(inst.key_resistance)} shifts to Bullish."
            ),
        }[inst.trend_bias]

        return [
            f"INSTRUMENT: {LABELS[symbol]}",
            f"LAST CLOSE: {fmt(p)} ({bar_date.strftime('%a %d %b %Y')})",
            "",
            "8 EMA vs PRICE:",
            f" - Price is {'ABOVE' if above8 else 'BELOW'} the 8 EMA. "
            f"{'Momentum intact short-term.' if above8 else 'Short-term momentum weakening.'}",
            f" - 8 EMA estimated at ~{fmt(e8)}. Price is ~{fmt(abs(p - e8))} points "
            f"{'above' if above8 else 'below'} it.",
            "",
            "8 EMA vs 21 EMA:",
            f" - 8 EMA is {'ABOVE' if above21 else 'BELOW'} 21 EMA. Trend structure {zone[1].lower()}.",
            f" - 21 EMA estimated at ~{fmt(e21)}. Gap between 8 and 21 EMA = ~{fmt(abs(e8 - e21))} pts.",
            f" - EMA condition: Zone {zone[0]} ({zone[1]}) — {zone[2]}.",
            "",
            "TRENDLINE:",
            f" - Trend assessed from recent swing lows over the last {LOOKBACK} sessions.",
            f" - Approximate trendline support: {fmt(inst.key_support)}–{fmt(e21)} on the coming week.",
            f" - Price is {'above' if p > inst.key_support else 'below'} key trend support. "
            f"{'No break detected.' if p > inst.key_support else 'Break detected — caution.'}",
            "",
            "KEY LEVELS:",
            f" - Resistance 1: {fmt(inst.key_resistance)} (20-day rolling swing high).",
            f" - Resistance 2: {fmt(inst.key_resistance * 1.02)} (extended target above recent highs).",
            f" - Support 1: {fmt(inst.key_support)} (20-day rolling swing low).",
            f" - Support 2: {fmt(inst.key_support * 0.98)} (secondary support below recent lows).",
            "",
            "BREADTH NOTE:",
            f" - Single-instrument read for {symbol}; cross-index breadth not computed in this scaffold.",
            " - Compare SPX, NDX, and IWM blocks for broadening vs narrow leadership.",
            "",
            f"TECHNICAL BIAS: {bias_text}",
            f"CONFIDENCE: {inst.confidence.value}. Structure {'clear' if inst.confidence == Confidence.HIGH else 'mixed'}.",
            f"INVALIDATION: {invalidation}",
            f"WATCH THIS WEEK: Can price hold {'above' if above8 else 'below'} the 8 EMA at {fmt(e8)}? "
            f"Does it {'break' if p < inst.key_resistance else 'hold'} {fmt(inst.key_resistance)} resistance?",
        ]

    def save_md(self, output: TechnicalOutput, prediction_date: date) -> None:
        """Render TechnicalOutput to MD matching data/formats/technical_agent.md"""
        week = prediction_date.isocalendar()
        filename = f"technical_agent_{week.year}-W{week.week:02d}.md"
        out_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "technical"
        out_dir.mkdir(parents=True, exist_ok=True)

        lines = [f"Technical Agent Output — Week of {prediction_date}", ""]
        symbols = list(output.instruments)
        for i, symbol in enumerate(symbols):
            bar_date = self._fetch_ohlcv(symbol, prediction_date).index[-1].date()
            lines.extend(self._render_block(symbol, output.instruments[symbol], bar_date))
            if i < len(symbols) - 1:
                lines.extend(["", "---", ""])

        (out_dir / filename).write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    prediction_date = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    agent = TechnicalAgent()
    output = agent.run(prediction_date)
    agent.export(output, prediction_date, fmt="json")
    agent.export(output, prediction_date, fmt="md")
    print(f"Saved to data/outputs/technical/")
