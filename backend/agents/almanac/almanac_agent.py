"""Almanac Agent - encodes seasonal data for a given prediction week."""

import json
import sys
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.almanac.almanac_data import MONTHLY_STATS, SECTOR_WINDOWS, SOURCE_NOTE
from agents.almanac.almanac_data import WEEKLY_PATTERNS
from agents.base import BaseAgent
from agents.schemas import AlmanacOutput, Bias, Confidence, SectorSignal

REPO_ROOT = Path(__file__).resolve().parents[3]
TITLE_DASH = "\u2014"
DATE_DASH = "\u2013"


class AlmanacAgent(BaseAgent):
    agent_type = "almanac"

    def lookup_seasonal_data(self, prediction_date: date) -> AlmanacOutput:
        """Return encoded seasonal data for the given prediction week."""
        month_data = MONTHLY_STATS.get(prediction_date.month, MONTHLY_STATS[6])
        week_data = self._get_week_data(prediction_date)

        return AlmanacOutput(
            prediction_date=prediction_date,
            monthly_bias=Bias(month_data["monthly_bias"]),
            seasonal_bias=Bias(week_data["seasonal_bias"]),
            confidence=Confidence(week_data["confidence"]),
            weekly_pattern=week_data["name"],
            sector_signals=[
                SectorSignal(
                    sector=item["sector"],
                    bias=Bias(item["bias"]),
                    window=item["window"],
                )
                for item in SECTOR_WINDOWS
            ],
            thesis=week_data["thesis"],
        )

    def run(self, prediction_date: date, **kwargs) -> AlmanacOutput:
        return self.lookup_seasonal_data(prediction_date)

    def save_json(self, output: AlmanacOutput, prediction_date: date) -> None:
        """Serialize output to data/outputs/almanac/{YYYY-WNN}.json."""
        week = prediction_date.isocalendar()
        filename = f"{week.year}-W{week.week:02d}.json"
        out_dir = REPO_ROOT / "data" / "outputs" / self.agent_type
        out_dir.mkdir(parents=True, exist_ok=True)
        with open(out_dir / filename, "w", encoding="utf-8") as f:
            json.dump(asdict(output), f, indent=2, default=str)

    def save_md(self, output: AlmanacOutput, prediction_date: date) -> None:
        """Render AlmanacOutput to markdown matching data/formats/almanac_agent.md."""
        week = prediction_date.isocalendar()
        filename = f"almanac_agent_W{week.week:02d}.md"
        out_dir = REPO_ROOT / "data" / "almanac"
        out_dir.mkdir(parents=True, exist_ok=True)

        month_data = MONTHLY_STATS.get(prediction_date.month, MONTHLY_STATS[6])
        week_data = self._get_week_data(prediction_date)
        week_start, week_end = self._week_bounds(prediction_date)
        period = self._format_period(week_start, week_end)
        sector_lines = self._render_sector_lines(output.sector_signals)
        weekly_lines = "\n".join(f"- {line}" for line in week_data["bullets"])

        content = f"""Almanac Agent Output {TITLE_DASH} Week of {period}

MONTH: {month_data["month"]} {prediction_date.year}
CYCLE CONTEXT: Midterm election year. Q2{DATE_DASH}Q3 remains the Almanac "Weak Spot" before the stronger Q4 period.

MONTHLY STATS:
- S&P 500: {month_data["sp500"]}
- Midterm year {month_data["month"]} context: {month_data["midterm"]}
- Nasdaq: {month_data["nasdaq"]}
- Russell 2000: {month_data["russell"]}

SPECIFIC WEEK PATTERN ({week_data["label"]}):
{weekly_lines}

SECTOR SIGNALS:
{sector_lines}

ALMANAC SEASONAL BIAS: {output.seasonal_bias.value}.
PATTERN CONFIDENCE: {output.confidence.value.upper()}. Data is useful as a background signal, but macro events and technical levels can override seasonality.
ALMANAC THESIS: "{output.thesis}"
INVALIDATION: A major macro surprise or technical breakout against the seasonal bias would reduce the value of this Almanac signal for the week.

Source: {SOURCE_NOTE}
"""
        (out_dir / filename).write_text(content, encoding="utf-8")

    def _get_week_data(self, prediction_date: date) -> dict:
        key = (prediction_date.month, self._week_of_month(prediction_date))
        if key in WEEKLY_PATTERNS:
            return WEEKLY_PATTERNS[key]

        month_data = MONTHLY_STATS.get(prediction_date.month, MONTHLY_STATS[6])
        return {
            "label": f"{month_data['month']} week",
            "name": "General monthly seasonal pattern",
            "bullets": [
                "No specific weekly pattern has been encoded yet for this date.",
                "Use the monthly seasonal bias as the base Almanac signal.",
                "Treat this as a low-confidence seasonal input until more data is added.",
            ],
            "seasonal_bias": month_data["monthly_bias"],
            "confidence": "Low",
            "thesis": (
                "Only the monthly Almanac context is encoded for this date, so the "
                "seasonal signal should be treated as a background input."
            ),
        }

    @staticmethod
    def _week_of_month(prediction_date: date) -> int:
        return ((prediction_date.day - 1) // 7) + 1

    @staticmethod
    def _week_bounds(prediction_date: date) -> tuple[date, date]:
        week_start = prediction_date - timedelta(days=prediction_date.weekday())
        week_end = week_start + timedelta(days=4)
        return week_start, week_end

    @staticmethod
    def _format_period(start: date, end: date) -> str:
        if start.month == end.month:
            return f"{start.day}{DATE_DASH}{end.day} {start:%B %Y}"
        return f"{start.day} {start:%B}{DATE_DASH}{end.day} {end:%B %Y}"

    @staticmethod
    def _render_sector_lines(signals: list[SectorSignal]) -> str:
        return "\n".join(
            f"- {signal.sector}: {signal.window} Bias: {signal.bias.value}."
            for signal in signals
        )


if __name__ == "__main__":
    prediction_date = (
        date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    )
    agent = AlmanacAgent()
    output = agent.run(prediction_date)
    agent.export(output, prediction_date, fmt="json")
    agent.export(output, prediction_date, fmt="md")
    print("Saved to data/outputs/almanac/ and data/almanac/")
