"""Almanac Agent.

This agent turns our encoded seasonal research into the normal agent output
format used by the project. It does not fetch live market data. The Almanac
numbers and notes live in almanac_data.py, and this file mainly decides which
month/week data to use for a given prediction date.

Basic flow:
1. Look up month and week data from almanac_data.py.
2. Convert that data into the AlmanacOutput schema.
3. Save the result as JSON for the app and Markdown for the weekly report.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

# This lets the file run directly from the command line without installing the
# backend package first. It points Python at the backend/ folder.
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.almanac.almanac_data import MONTHLY_STATS, SECTOR_WINDOWS, SOURCE_NOTE
from agents.almanac.almanac_data import WEEKLY_PATTERNS
from core.base import BaseAgent
from core.io import FileSaver, week_stem
from core.schemas import AlmanacOutput, Bias, Confidence, SectorSignal

REPO_ROOT = Path(__file__).resolve().parents[3]

# Keep these as escaped characters so the code file stays plain ASCII while
# the generated Markdown still matches the teacher's required template.
TITLE_DASH = "\u2014"
DATE_DASH = "\u2013"


class AlmanacAgent(BaseAgent):
    """Seasonality agent for Stock Trader's Almanac style data."""

    # FileSaver uses this name when saving JSON under data/outputs/almanac/.
    agent_type = "almanac"

    def lookup_seasonal_data(self, prediction_date: date, horizon_days: int = 7) -> AlmanacOutput:
        """Build the structured AlmanacOutput for one prediction date.

        prediction_date can be any date inside the target prediction week. The
        agent uses the month and week-of-month to pick the closest encoded
        Almanac entry.
        """
        if horizon_days <= 7:
            # Month data gives the broad seasonal background, for example whether
            # June is normally weak in a midterm year.
            month_data = MONTHLY_STATS.get(prediction_date.month, MONTHLY_STATS[6])

            # Week data gives the more specific pattern, for example mid-June or
            # early-July behavior. If no weekly pattern exists, _get_week_data()
            # falls back to the month-level signal.
            week_data = self._get_week_data(prediction_date)
        else:
            month_data, week_data = self._lookup_horizon_data(prediction_date, horizon_days)

        # The schema classes use enums such as Bias and Confidence, so convert
        # the plain strings from almanac_data.py into those enum values here.
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
            horizon_days=horizon_days,
        )

    def run(self, prediction_date: date, **kwargs) -> AlmanacOutput:
        """Entry point required by BaseAgent."""
        horizon_days = int(kwargs.get("horizon_days", 7))
        return self.lookup_seasonal_data(prediction_date, horizon_days=horizon_days)

    def render_md(self, output: AlmanacOutput, prediction_date: date) -> str:
        """Return Markdown matching data/formats/almanac_agent.md."""
        # Re-read the raw dicts because the Markdown needs details that are not
        # stored directly inside AlmanacOutput, such as the full monthly stats
        # text and the weekly bullet list.
        month_data = MONTHLY_STATS.get(prediction_date.month, MONTHLY_STATS[6])
        week_data = self._get_week_data(prediction_date)

        # The report title should show the full Monday-Friday prediction week,
        # not just the single date passed on the command line.
        week_start, week_end = self._horizon_bounds(prediction_date, output.horizon_days)
        period = self._format_period(week_start, week_end)

        # Build each Markdown section separately so the big template below stays
        # readable and close to the teacher's required format.
        sector_lines = self._render_sector_lines(output.sector_signals)
        monthly_lines = self._render_monthly_lines(month_data)
        weekly_lines = "\n".join(f"- {line}" for line in week_data["bullets"])

        return f"""Almanac Agent Output {TITLE_DASH} Week of {period}

MONTH: {month_data["month"]} {prediction_date.year}
CYCLE CONTEXT: Midterm election year. Q2{DATE_DASH}Q3 remains the Almanac "Weak Spot" before the stronger Q4 period.

MONTHLY STATS:
{monthly_lines}

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

    def _get_week_data(self, prediction_date: date) -> dict:
        """Find the weekly seasonal pattern for the given date.

        WEEKLY_PATTERNS is keyed by (month, week_of_month), for example
        (6, 3) means the third week of June. This is simple enough for our
        sprint use case and easy for data encoders to update.
        """
        key = (prediction_date.month, self._week_of_month(prediction_date))
        if key in WEEKLY_PATTERNS:
            return WEEKLY_PATTERNS[key]

        # Not every future week has a specific Almanac pattern encoded yet.
        # When that happens, still return a valid low-confidence output instead
        # of crashing. This is better for demos and for incomplete data.
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

    def _lookup_horizon_data(
            self, prediction_date: date, horizon_days: int
    ) -> tuple[dict, dict]:
        """Aggregate month/week Almanac patterns over [prediction_date, +horizon).
        week_data uses the same keys as _get_week_data():
        label, name, bullets, seasonal_bias, confidence, thesis
        """
        start = prediction_date
        end = prediction_date + timedelta(days=horizon_days - 1)
        patterns: list[dict] = []
        seen: set[tuple[int, int]] = set()

        def _add(day: date) -> None:
            key = (day.month, self._week_of_month(day))
            if key in seen:
                return
            seen.add(key)
            patterns.append(self._get_week_data(day))

        day = start
        while day <= end:
            _add(day)
            day += timedelta(days=7)
        _add(end)
        # Midpoint month for monthly_bias
        mid = start + timedelta(days=(end - start).days // 2)
        month_data = MONTHLY_STATS.get(mid.month, MONTHLY_STATS[6])
        biases = [p["seasonal_bias"] for p in patterns]
        counts: dict[str, int] = {}
        for bias in biases:
            counts[bias] = counts.get(bias, 0) + 1
        top_count = max(counts.values())
        leaders = [bias for bias, n in counts.items() if n == top_count]
        seasonal_bias = leaders[0] if len(leaders) == 1 else "Mixed"
        conf_rank = {"High": 3, "Medium": 2, "Low-Medium": 1.5, "Low": 1}
        if len(set(biases)) > 1:
            confidence = "Low"
        else:
            confidence = min(
                patterns,
                key=lambda p: conf_rank.get(p["confidence"], 1),
            )["confidence"]
        names = [p["name"] for p in patterns]
        labels = [p["label"] for p in patterns]
        bullets: list[str] = []
        for p in patterns:
            bullets.extend(p.get("bullets", [])[:2])
        if not bullets:
            bullets = [
                f"Seasonal window covers {horizon_days} days from {start} to {end}."
            ]
        week_data = {
            "label": " + ".join(labels),
            "name": " + ".join(names) + f" ({horizon_days}-day window)",
            "bullets": bullets,
            "seasonal_bias": seasonal_bias,
            "confidence": confidence,
            "thesis": (
                f"Over the next {horizon_days} days ({start} to {end}), "
                f"Almanac patterns ({', '.join(names)}) aggregate to a "
                f"{seasonal_bias.lower()} seasonal lean."
            ),
        }
        return month_data, week_data

    @staticmethod
    def _week_of_month(prediction_date: date) -> int:
        """Convert a calendar day into a simple week number inside the month."""
        return ((prediction_date.day - 1) // 7) + 1

    @staticmethod
    def _week_bounds(prediction_date: date) -> tuple[date, date]:
        """Return the Monday-Friday range for the prediction week."""
        week_start = prediction_date - timedelta(days=prediction_date.weekday())
        week_end = week_start + timedelta(days=4)
        return week_start, week_end

    @staticmethod
    def _horizon_bounds(prediction_date: date, horizon_days: int) -> tuple[date, date]:
        if horizon_days <= 7:
            return AlmanacAgent._week_bounds(prediction_date)
        start = prediction_date
        end = prediction_date + timedelta(days=horizon_days - 1)
        return start, end

    @staticmethod
    def _format_period(start: date, end: date) -> str:
        """Format a week range for the Markdown title."""
        if start.month == end.month:
            return f"{start.day}{DATE_DASH}{end.day} {start:%B %Y}"
        return f"{start.day} {start:%B}{DATE_DASH}{end.day} {end:%B %Y}"

    def _render_monthly_lines(self, month_data: dict) -> str:
        """Render the four required monthly-stat bullets."""
        return "\n".join(
            [
                f"- S&P 500: {self._format_index_stat(month_data['sp500'])}",
                (
                    f"- Midterm year {month_data['month']} context: "
                    f"{self._format_midterm_stat(month_data['midterm'])}"
                ),
                f"- Nasdaq: {self._format_index_stat(month_data['nasdaq'])}",
                f"- Russell 2000: {self._format_index_stat(month_data['russell'])}",
            ]
        )

    @staticmethod
    def _format_index_stat(stat: dict) -> str:
        """Turn one index-stat dict into one readable sentence.

        Some monthly figures are not verified yet. In that case we still render
        the available note and clearly say that data encoder verification is
        needed.
        """
        pieces = []
        if stat.get("rank") is not None:
            pieces.append(f"ranks #{stat['rank']} of 12 months")
        if stat.get("up_pct") is not None:
            pieces.append(f"up {stat['up_pct']}% of the time")
        if stat.get("avg_return") is not None:
            pieces.append(f"Avg {stat['avg_return']:+.1f}% normally")
        if stat.get("note"):
            pieces.append(stat["note"])
        if not stat.get("verified"):
            pieces.append("Exact page figure still needs encoder verification")
        return ". ".join(piece.rstrip(".") for piece in pieces) + "."

    @staticmethod
    def _format_midterm_stat(stat: dict) -> str:
        """Format the special midterm-year S&P 500 context."""
        pieces = []
        if stat.get("rank") is not None:
            pieces.append(f"ranks #{stat['rank']} in the midterm-year pattern")
        if stat.get("avg_return") is not None:
            pieces.append(f"Avg {stat['avg_return']:+.1f}% for S&P 500")
        if stat.get("note"):
            pieces.append(stat["note"])
        if not stat.get("verified"):
            pieces.append("Exact midterm page figure still needs encoder verification")
        return ". ".join(piece.rstrip(".") for piece in pieces) + "."

    @staticmethod
    def _render_sector_lines(signals: list[SectorSignal]) -> str:
        """Render sector signals as Markdown bullets."""
        return "\n".join(
            f"- {signal.sector}: {signal.window} Bias: {signal.bias.value}."
            for signal in signals
        )


    @classmethod
    def parse_md(cls, text: str, prediction_date: date | None = None) -> AlmanacOutput:
        import re
        from agents import md_parsing as mdp

        # prediction_date from "Week of 15–19 June 2026" in title
        m = re.search(r"Week of (\d{1,2})[–-](\d{1,2}) ([A-Z][a-z]+) (\d{4})", text)
        if m:
            pred = date(int(m.group(4)), mdp._MONTH_MAP.get(m.group(3)[:3].lower(), 6), int(m.group(1)))
        else:
            pred = prediction_date or date.today()

        seasonal_raw = mdp.first(r"ALMANAC SEASONAL BIAS:\s*(\w+)", text)
        confidence_raw = mdp.first(r"PATTERN CONFIDENCE:\s*([A-Za-z–—-]+)", text)
        thesis_raw = mdp.first(r'ALMANAC THESIS:\s*"(.+?)"', text) or ""
        pattern_label = mdp.first(r"SPECIFIC WEEK PATTERN \(([^)]+)\)", text) or ""

        # monthly_bias: look for "MONTH: (month)" and infer from known data
        month_match = re.search(r"MONTH:\s*([A-Z][a-z]+)", text)
        monthly = "Mixed"
        if month_match:
            mn = month_match.group(1)[:3].lower()
            monthly_map = {"may": "Mixed", "jun": "Bearish", "jul": "Mixed", "dec": "Bullish"}
            monthly = monthly_map.get(mn, "Mixed")

        # sector_signals from "SECTOR SIGNALS:" section
        sectors = []
        in_sectors = False
        for line in text.split("\n"):
            if "SECTOR SIGNALS:" in line:
                in_sectors = True
                continue
            if in_sectors and line.startswith("- "):
                sm = re.match(r"- (.+?): (.+?) Bias: (\w+)\.", line)
                if sm:
                    sectors.append(SectorSignal(
                        sector=sm.group(1).strip(),
                        window=sm.group(2).strip(),
                        bias=Bias(sm.group(3).title()),
                    ))
            elif in_sectors and not line.startswith("- "):
                in_sectors = False

        return AlmanacOutput(
            prediction_date=pred,
            monthly_bias=Bias(monthly),
            seasonal_bias=Bias(mdp.norm_bias(seasonal_raw or "")),
            confidence=Confidence(mdp.norm_confidence(confidence_raw or "")),
            thesis=thesis_raw,
            weekly_pattern=pattern_label,
            sector_signals=sectors,
        )


if __name__ == "__main__":
    # Example:
    #   python backend/agents/almanac/almanac_agent.py 2026-06-16
    #
    # If no date is provided, it uses today's date. Passing the date is better
    # for coursework because every run should be reproducible.
    prediction_date = (
        date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    )
    agent = AlmanacAgent()
    output = agent.run(prediction_date)
    json_saver = FileSaver(REPO_ROOT / "data" / "outputs" / agent.agent_type)
    json_saver.save(agent.render_json(output, prediction_date), f"{week_stem(prediction_date)}.json")

    md_dir = REPO_ROOT / "data" / "almanac"
    md_saver = FileSaver(md_dir)
    md_saver.save(agent.render_md(output, prediction_date), f"almanac_agent_{week_stem(prediction_date)}.md")
    print("Saved to data/outputs/almanac/ and data/almanac/")
