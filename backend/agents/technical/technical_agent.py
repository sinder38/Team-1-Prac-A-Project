"""
Technical Agent — fetches price data and computes EMA-based technical analysis.

Usage:
    python agents/technical/technical_agent.py 2026-06-16
"""
from datetime import date
from dataclasses import dataclass
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base import BaseAgent
from agents.schemas import TechnicalOutput, InstrumentTechnical, Bias, Confidence

INSTRUMENTS = ["SPX", "NDX", "IWM"]


class TechnicalAgent(BaseAgent):
    agent_type = "technical"

    def fetch_instrument(self, symbol: str, prediction_date: date) -> InstrumentTechnical:
        """
        Fetch price data and compute EMAs for a single instrument.
        TODO: implement using yfinance or similar.
        """
        raise NotImplementedError(f"fetch_instrument not implemented for {symbol}")

    def run(self, prediction_date: date, instruments: list[str] = INSTRUMENTS, **kwargs) -> TechnicalOutput:
        results = {}
        for symbol in instruments:
            results[symbol] = self.fetch_instrument(symbol, prediction_date)
        return TechnicalOutput(prediction_date=prediction_date, instruments=results)

    def render_md(self, output: TechnicalOutput, prediction_date: date) -> str:
        lines = [f"Technical Agent Output — Week of {prediction_date}", ""]
        for symbol, inst in output.instruments.items():
            lines += [
                f"INSTRUMENT: {symbol}",
                f"LAST CLOSE: {inst.last_close}",
                f"8 EMA: {inst.ema_8}",
                f"21 EMA: {inst.ema_21}",
                f"TECHNICAL BIAS: {inst.trend_bias.value}",
                f"KEY SUPPORT: {inst.key_support}",
                f"KEY RESISTANCE: {inst.key_resistance}",
                f"CONFIDENCE: {inst.confidence.value}",
                "",
            ]
        return "\n".join(lines)


if __name__ == "__main__":
    from agents.io import FileSaver, week_stem
    prediction_date = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    agent = TechnicalAgent()
    output = agent.run(prediction_date)
    saver = FileSaver.for_agent(agent.agent_type)
    saver.save(agent.render_json(output, prediction_date), f"{week_stem(prediction_date)}.json")
    print(f"Saved to data/outputs/technical/")
