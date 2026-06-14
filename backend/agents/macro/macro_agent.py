"""
Macro Agent — fetches Fed rates, yields, commodities, and macro calendar data.

Usage:
    python agents/macro/macro_agent.py 2026-06-16
"""
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base import BaseAgent
from agents.schemas import MacroOutput, MacroBias, Confidence


class MacroAgent(BaseAgent):
    agent_type = "macro"

    def fetch_macro_data(self, prediction_date: date) -> MacroOutput:
        """
        Fetch Fed rate, Treasury yields, DXY, and build macro output.
        TODO: implement using yfinance, FRED API, or similar free sources.
        See data/formats/macro_agent.md for expected output shape.
        """
        raise NotImplementedError("fetch_macro_data not implemented")

    def run(self, prediction_date: date, **kwargs) -> MacroOutput:
        return self.fetch_macro_data(prediction_date)

    def render_md(self, output: MacroOutput, prediction_date: date) -> str:
        return f"""Macro Agent Output — Week of {prediction_date}

FED & RATES:
 · Current Fed rate: {output.fed_rate}
 · 2-year yield: {output.yield_2y}%
 · 10-year yield: {output.yield_10y}%
 · 30-year yield: {output.yield_30y}%

DOLLAR:
 · DXY: {output.dxy}

MACRO BIAS: {output.macro_bias.value if output.macro_bias else "N/A"}
PRIMARY DRIVER THIS WEEK: {output.primary_driver}
CONFIDENCE: {output.confidence.value if output.confidence else "N/A"}
INVALIDATION: {output.invalidation}
"""


if __name__ == "__main__":
    from agents.io import FileSaver, week_stem

    prediction_date = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    agent = MacroAgent()
    output = agent.run(prediction_date)
    saver = FileSaver.for_agent(agent.agent_type)
    saver.save(agent.render_json(output, prediction_date), f"{week_stem(prediction_date)}.json")
    print(f"Saved to data/outputs/macro/")
