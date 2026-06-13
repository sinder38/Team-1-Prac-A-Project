"""
Almanac Agent — encodes Stock Trader's Almanac seasonal data for a given week.

Usage:
    python agents/almanac/almanac_agent.py 2026-06-16
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base import BaseAgent
from agents.schemas import AlmanacOutput, Bias, Confidence, SectorSignal


class AlmanacAgent(BaseAgent):
    agent_type = "almanac"

    def lookup_seasonal_data(self, prediction_date: date) -> AlmanacOutput:
        """
        Return seasonal data for the given prediction week.
        TODO: implement by encoding almanac data as Python dicts keyed by (month, week_of_month).
        See data/formats/almanac_agent.md for expected output shape.
        """
        raise NotImplementedError("lookup_seasonal_data not implemented")

    def run(self, prediction_date: date, **kwargs) -> AlmanacOutput:
        return self.lookup_seasonal_data(prediction_date)

    def render_md(self, output: AlmanacOutput, prediction_date: date) -> str:
        sector_lines = "\n".join(
            f" - {s.sector}: {s.bias.value} — {s.window}" for s in output.sector_signals
        )
        return f"""Almanac Agent Output — Week of {prediction_date}

MONTHLY BIAS: {output.monthly_bias.value if output.monthly_bias else "N/A"}
WEEKLY PATTERN: {output.weekly_pattern}
SEASONAL BIAS: {output.seasonal_bias.value if output.seasonal_bias else "N/A"}
CONFIDENCE: {output.confidence.value if output.confidence else "N/A"}

SECTOR SIGNALS:
{sector_lines}

ALMANAC THESIS: {output.thesis}
"""


if __name__ == "__main__":
    from agents.io import FileSaver, week_stem

    prediction_date = (
        date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    )
    agent = AlmanacAgent()
    output = agent.run(prediction_date)
    saver = FileSaver.for_agent(agent.agent_type)
    saver.save(
        agent.render_json(output, prediction_date), f"{week_stem(prediction_date)}.json"
    )
    print(f"Saved to data/outputs/almanac/")
