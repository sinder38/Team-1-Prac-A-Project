"""
Macro Agent — fetches Fed rates, yields, commodities, and macro calendar data.

Usage:
    Add Api_key (either by .env file or by command)
    python backend/agents/macro/macro_agent.py 2026-06-16
"""
import json
import re
import sys
from csv import DictReader
from datetime import date, datetime
from dataclasses import asdict
from io import StringIO
from pathlib import Path
import requests
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv

from agents import md_parsing as md
from agents.macro.macro_event_data import Event
from agents.macro.macro_sources import (
    ConfirmedNewsSource,
    EarningsWhispersCalendar,
    FedWatchSource,
    TradingEconomicsCalendar,
    MacroFetchError,
)
from agents.base import BaseAgent
from agents.paths import DATA_DIR, OUTPUTS_DIR
from agents.schemas import (
    CalendarEvent,
    CommodityData,
    Confidence,
    MacroBias,
    MacroOutput,
)

load_dotenv()

# The direction is captured with [ \t] (not \s) and \w* so an empty direction
# does not spill across the newline into the next section's first word.
_COMMODITY_RE = {
    "wti_oil": r"WTI Crude Oil:\s*([\d,\.]+),\s*weekly change\s*([+-]?[\d.]+)%,\s*direction:[ \t]*(\w*)",
    "gold": r"Gold:\s*([\d,\.]+),\s*weekly change\s*([+-]?[\d.]+)%,\s*direction:[ \t]*(\w*)",
    "dxy": r"DXY \(Dollar\):\s*([\d,\.]+),\s*weekly change\s*([+-]?[\d.]+)%,\s*direction:[ \t]*(\w*)",
}

_CAL_RE = re.compile(
    r"^-\s*(?P<date_label>.+?):\s*(?P<name>.+?)\s*—\s*Expected:\s*(?P<expected>.*?),"
    r"\s*Previous:\s*(?P<previous>.*?)\s*—\s*(?:IMPORTANCE|Impact):\s*(?P<impact>[A-Za-z]+)",
    re.M,
)


def _date_from_md(text: str) -> date | None:
    """Read the prediction date from the "Sources accessed: <ISO>" footer."""
    m = re.search(r"Sources accessed:\s*(\d{4}-\d{2}-\d{2})", text)
    if not m:
        return None
    try:
        return date.fromisoformat(m.group(1))
    except ValueError:
        return None


def _strip_md_link(text: str) -> str:
    """'[name](url)' -> 'name'; leaves plain text unchanged."""
    return re.sub(r"^\[(.*?)\]\(.*?\)$", r"\1", text.strip())


def _commodity(text: str, pattern: str) -> "CommodityData":
    m = re.search(pattern, text)
    if not m:
        return CommodityData(price=0.0, weekly_change=0.0, direction="")
    return CommodityData(
        price=md.num(m.group(1)),
        weekly_change=float(m.group(2)),
        direction=m.group(3),
    )


def _bullets(text: str, header: str) -> list[str]:
    """Collect '- ' bullet lines under a section header up to the next header."""
    out: list[str] = []
    capturing = False
    for line in text.splitlines():
        if header in line:
            capturing = True
            continue
        if capturing:
            stripped = line.strip()
            if stripped.startswith("- "):
                out.append(stripped)
            elif stripped and stripped[0].isupper() and stripped.endswith(":"):
                break
            elif re.match(r"^[A-Z][A-Z &/]+", stripped) and ":" in stripped:
                break
    return out


class MacroAgent(BaseAgent):
    agent_type = "macro"

    def __init__(
            self,
            calendar_source: TradingEconomicsCalendar | None = None,
            news_source: ConfirmedNewsSource | None = None,
            earnings_source: EarningsWhispersCalendar | None = None,
            fedwatch_source: FedWatchSource | None = None,
    ):
        self.calendar_source = calendar_source or TradingEconomicsCalendar()
        self.news_source = news_source or ConfirmedNewsSource()
        self.earnings_source = earnings_source or EarningsWhispersCalendar()
        self.fedwatch_source = fedwatch_source or FedWatchSource()

    @staticmethod
    def report_week_label(prediction_date: date) -> str:
        """Return a human-readable report week label."""
        return f"{prediction_date.day} {prediction_date.strftime('%B')}"

    @staticmethod
    def full_date_label(value: date | None) -> str:
        """Return a report-friendly date label."""
        if value is None:
            return "N/A"
        return f"{value.strftime('%B')} {value.day}, {value.year}"

    @staticmethod
    def direction_from_change(
            change: float,
            positive: str = "rising",
            negative: str = "falling",
            flat: str = "flat",
            threshold: float = 0.0,
    ) -> str:
        """Map a numeric weekly change to a direction label."""
        if change > threshold:
            return positive
        if change < -threshold:
            return negative
        return flat

    @staticmethod
    def determine_yield_curve(yield_2y: float, yield_10y: float) -> str:
        """Classify the 2years10years yield curve."""
        spread = yield_10y - yield_2y
        if spread > 0.05:
            return "normal"
        if spread < -0.05:
            return "inverted"
        return "flat"

    @staticmethod
    def format_price(value: float) -> str:
        """Format market prices without noisy trailing zeroes."""
        return f"{value:.2f}".rstrip("0").rstrip(".")

    @staticmethod
    def format_percent(value: float) -> str:
        """Format weekly percentage moves with explicit signs."""
        return f"{value:+.2f}%"

    def fetch_fred_observations(self, series: str) -> list[tuple[date, float]]:
        """Fetch FRED observations from the public no-key CSV endpoint."""
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
        except requests.RequestException as e:
            raise MacroFetchError(f"Failed to fetch FRED series {series}: {e}") from e
        observations: list[tuple[date, float]] = []
        for row in DictReader(StringIO(response.text)):
            value = row.get(series)
            if not value or value == ".":
                continue
            observations.append((date.fromisoformat(row["observation_date"]), float(value)))
        return observations

    def fetch_fred(self, series: str) -> float | None:
        """Fetch latest observation from FRED without requiring an API key."""
        observations = self.fetch_fred_observations(series)
        return observations[-1][1] if observations else None

    def fetch_fred_weekly_change(self, series: str) -> float:
        """Weekly change in percentage points for FRED series."""
        observations = self.fetch_fred_observations(series)
        if len(observations) >= 6:
            return round(observations[-1][1] - observations[-6][1], 2)
        return 0.0

    def get_fed_rate(self) -> str:
        """Get current Fed rate (lower and upper bound)."""
        low = self.fetch_fred("DFEDTARL")
        high = self.fetch_fred("DFEDTARU")
        if low is None or high is None:
            raise MacroFetchError("FRED returned no observations for DFEDTARL/DFEDTARU")
        return f"{low:.2f}%-{high:.2f}%"

    def get_yields(self) -> dict:
        """Get Treasury yields: 2-year, 10-year, 30-year."""
        yield_2y = self.fetch_fred("DGS2")
        yield_10y = self.fetch_fred("DGS10")
        yield_30y = self.fetch_fred("DGS30")
        return {
            "2y": yield_2y if yield_2y is not None else 0.0,
            "10y": yield_10y if yield_10y is not None else 0.0,
            "30y": yield_30y if yield_30y is not None else 0.0,
        }

    def latest_price(self, ticker: str) -> float | None:
        """Get latest closing price for a ticker."""
        try:
            price = yf.Ticker(ticker).history(period="5d")["Close"].iloc[-1]
        except Exception as e:
            raise MacroFetchError(f"Failed to fetch price for {ticker}: {e}") from e
        if pd.isna(price):
            raise MacroFetchError(f"yfinance returned no price data for {ticker}")
        return float(price)

    def get_weekly_return(self, ticker: str) -> float:
        """Get weekly return for a single ticker (last close vs 5 trading days ago)."""
        try:
            raw = yf.download(ticker, period="1mo", interval="1d", auto_adjust=True)
        except Exception as e:
            raise MacroFetchError(f"Failed to fetch weekly return for {ticker}: {e}") from e
        if raw is None or raw.empty:
            raise MacroFetchError(f"yfinance returned no data for {ticker}")
        data = raw["Close"]
        if isinstance(data, pd.Series):
            data = data.to_frame()
        s = data[ticker].dropna() if isinstance(data, pd.DataFrame) else data.dropna()
        if len(s) < 6:
            raise MacroFetchError(f"yfinance returned insufficient trading days for {ticker}")
        return round((s.iloc[-1] / s.iloc[-6] - 1) * 100, 4)

    def fetch_commodity_data(
            self,
            ticker: str,
            positive_direction: str = "rising",
            negative_direction: str = "falling",
            flat_direction: str = "flat",
    ) -> CommodityData:
        """Fetch commodity price and weekly change."""
        price = self.latest_price(ticker)
        weekly_change = self.get_weekly_return(ticker)

        return CommodityData(
            price=round(price, 4),
            weekly_change=weekly_change,
            direction=self.direction_from_change(
                weekly_change,
                positive=positive_direction,
                negative=negative_direction,
                flat=flat_direction,
            ),
        )

    def fetch_upcoming_events(self, prediction_date: date, horizon_days: int = 7) -> list[Event]:
        """Fetch next week's five most important TradingEconomics events."""
        return self.calendar_source.get_top_events(prediction_date, horizon_days=horizon_days)

    def build_week_ahead_calendar(self, events: list[Event]) -> list[CalendarEvent]:
        """Convert sourced events to schema objects for export."""
        return [
            CalendarEvent(
                date_label=event.date_label,
                name=event.name,
                impact=event.impact.title(),
                expected=event.expected,
                previous=event.previous,
                priority=event.priority,
                source_url=event.source_url,
            )
            for event in events
        ]

    def build_primary_driver(self, events: list[Event]) -> str:
        """Describe the top-priority event as the report's primary driver."""
        if not events:
            return "- No major scheduled events"

        primary_event = max(events, key=lambda e: e.priority)
        driver_name = primary_event.catalyst_name or primary_event.name
        driver_date = primary_event.catalyst_date or primary_event.date_label
        catalyst_type = "data" if any(
            token in driver_name.upper()
            for token in ("CPI", "PPI", "PAYROLLS", "INFLATION")
        ) else "event"
        return (
            f"{driver_name} {catalyst_type} on {driver_date} "
        )

    def build_invalidation(self, macro_bias: MacroBias) -> str:
        """Build an invalidation statement according to the report."""
        if macro_bias == MacroBias.BINARY_RISK:
            return (
                "If the marquee event lands close to consensus and cross-asset "
                "markets remain orderly, the binary-risk stance should fade back "
                "toward the underlying macro trend."
            )
        if macro_bias == MacroBias.HAWKISH:
            return (
                "Softer inflation, weaker labor data, or a clear drop in yields "
                "and the dollar would invalidate the hawkish bias."
            )
        if macro_bias == MacroBias.DOVISH:
            return (
                "Hotter inflation, stronger growth data, or a renewed rise in "
                "front-end yields would invalidate the dovish bias."
            )
        return (
            "A decisive move in yields, the dollar, or inflation expectations "
            "would invalidate the neutral macro read."
        )

    def determine_macro_bias(
            self,
            yield_2y_change: float,
            yield_10y_change: float,
            dxy_change: float,
            gold_change: float,
            wti_change: float,
    ) -> tuple[MacroBias, int]:
        """Determine macro bias using a scoring system based on weekly changes."""
        score = 0

        # Dollar strength
        if dxy_change > 1.25:
            score += 1
        elif dxy_change < -1.25:
            score -= 1

        # Front-end rates (2-year)
        if yield_2y_change > 0.20:
            score += 2
        elif yield_2y_change < -0.20:
            score -= 2

        # Long-end rates (10-year)
        if yield_10y_change > 0.15:
            score += 1
        elif yield_10y_change < -0.15:
            score -= 1

        # Gold (inverse relationship)
        if gold_change > 1.5:
            score -= 1
        elif gold_change < -1.5:
            score += 1

        # Oil
        if wti_change > 6.5:
            score += 1
        elif wti_change < -6.5:
            score -= 1

        # Determine bias based on score
        if score >= 4:
            bias = MacroBias.HAWKISH
        elif score <= -4:
            bias = MacroBias.DOVISH
        else:
            bias = MacroBias.NEUTRAL

        return bias, score

    def calculate_event_risk(self, events):
        """Calculate Event Risk."""
        score = 0

        for event in events:
            impact = event.impact.upper()
            if impact == "HIGH":
                score += 2
            elif impact == "MEDIUM":
                score += 1

        return score

    def is_exceptional_event_week(self, events: list[Event]) -> bool:
        """Reserve Binary-risk for rare, high-conviction event clusters."""
        if len(events) < 4:
            return False

        high_impact_events = [event for event in events if event.impact.upper() == "HIGH"]
        if len(high_impact_events) < 4:
            return False

        top_priority = max(event.priority for event in events)
        average_priority = sum(event.priority for event in events) / len(events)
        return (
            top_priority >= 85
            and average_priority >= 80
            and self.calculate_event_risk(events) >= 16
        )

    def fetch_macro_data(self, prediction_date: date, horizon_days: int = 7) -> MacroOutput:
        """
        Fetch Fed rate, Treasury yields, DXY, WTI, and Gold with weekly changes.
        Uses no-key FRED CSV downloads for rates/yields and yfinance for commodities.
        """
        # Fed rate
        fed_rate = self.get_fed_rate()

        # Treasury yields (current levels)
        yields = self.get_yields()
        yield_2y = yields["2y"]
        yield_10y = yields["10y"]
        yield_30y = yields["30y"]

        # Treasury yield changes (weekly)
        yield_2y_change = self.fetch_fred_weekly_change("DGS2")
        yield_10y_change = self.fetch_fred_weekly_change("DGS10")

        # Fetch all commodities with price and weekly change
        dxy_data = self.fetch_commodity_data("DX-Y.NYB")
        wti_data = self.fetch_commodity_data("CL=F")
        gold_data = self.fetch_commodity_data("GC=F")

        # Determine macro bias and score
        macro_bias, score = self.determine_macro_bias(
            yield_2y_change=yield_2y_change,
            yield_10y_change=yield_10y_change,
            dxy_change=dxy_data.weekly_change,
            gold_change=gold_data.weekly_change,
            wti_change=wti_data.weekly_change,
        )

        # Confidence based on score magnitude
        abs_score = abs(score)
        if abs_score >= 5:
            confidence = Confidence.HIGH
        elif abs_score >= 3:
            confidence = Confidence.MEDIUM
        else:
            confidence = Confidence.LOW

        upcoming_events = self.fetch_upcoming_events(prediction_date, horizon_days)
        key_earnings = [
            self.earnings_source.render_event(event)
            for event in self.earnings_source.get_key_events(prediction_date)
        ]
        confirmed_news = [
            self.news_source.render_item(item)
            for item in self.news_source.get_ranked_items()
        ]
        fomc_pricing = self.fedwatch_source.get_pricing()

        # Binary-risk is reserved for unusually concentrated, high-conviction event weeks.
        if self.is_exceptional_event_week(upcoming_events):
            macro_bias = MacroBias.BINARY_RISK
            confidence = Confidence.MEDIUM

        primary_driver = self.build_primary_driver(upcoming_events)
        invalidation = self.build_invalidation(macro_bias)

        return MacroOutput(
            prediction_date=prediction_date,
            fed_rate=fed_rate,
            yield_2y=round(yield_2y, 3),
            yield_10y=round(yield_10y, 3),
            yield_30y=round(yield_30y, 3),
            dxy=dxy_data,
            wti_oil=wti_data,
            gold=gold_data,
            macro_bias=macro_bias,
            primary_driver=primary_driver,
            confidence=confidence,
            invalidation=invalidation,
            next_fomc_date=fomc_pricing.next_fomc_date,
            hold_probability=fomc_pricing.hold_probability,
            cut_probability=fomc_pricing.cut_probability,
            fomc_direction=fomc_pricing.direction_vs_last_week,
            yield_curve=self.determine_yield_curve(yield_2y, yield_10y),
            yield_10y_direction=self.direction_from_change(yield_10y_change),
            week_ahead_calendar=self.build_week_ahead_calendar(upcoming_events),
            key_earnings=key_earnings,
            confirmed_news=confirmed_news,
            horizon_days=horizon_days,
        )

    def run(self, prediction_date: date, **kwargs) -> MacroOutput:
        horizon_days = int(kwargs.get("horizon_days", 7))
        return self.fetch_macro_data(prediction_date, horizon_days=horizon_days)

    def save_json(self, output: MacroOutput, prediction_date: date) -> None:
        """Serialize output to data/outputs/macro/{YYYY-WNN}.json."""
        week = prediction_date.isocalendar()
        filename = f"{week.year}-W{week.week:02d}.json"
        out_dir = OUTPUTS_DIR / self.agent_type
        out_dir.mkdir(parents=True, exist_ok=True)
        with open(out_dir / filename, "w", encoding="utf-8") as f:
            json.dump(asdict(output), f, indent=2, default=str)

    def render_calendar_events(self, output: MacroOutput) -> str:
        """Render week-ahead calendar rows."""
        if not output.week_ahead_calendar:
            return "- No high-impact macro calendar events were fetched from TradingEconomics."

        return "\n\n".join(
            (
                f"- {event.date_label}: {event.name} — Expected: "
                f"{event.expected}, Previous: {event.previous} — "
                f"IMPORTANCE: {event.impact} — Priority: {event.priority}/100"
            )
            for event in output.week_ahead_calendar
        )

    def render_key_earnings(self, output: MacroOutput) -> str:
        """Render key earnings rows."""
        if not output.key_earnings:
            return "- No key earnings data was fetched from Earnings Whispers or TradingEconomics."

        return "\n\n".join(output.key_earnings)

    def render_confirmed_news(self, output: MacroOutput) -> str:
        """Render confirmed NewsData.io news rows."""
        if not output.confirmed_news:
            return "- No Reuters/AP headlines were fetched from NewsData.io. Set NEWSDATA_API_KEY to enable confirmed news."

        return "\n\n".join(output.confirmed_news)

    def render_md(self, output: MacroOutput, prediction_date: date) -> str:
        """Return the markdown string for this output (satisfies BaseAgent contract)."""
        return f"""Macro Agent Output — Week of {self.report_week_label(prediction_date)} — Source: R4

FED & RATES (FRED & Yfinance):

- Current Fed rate: {output.fed_rate}
- Next FOMC date: {self.full_date_label(output.next_fomc_date)}. Hold probability: {output.hold_probability:.1f}%. Cut probability: {output.cut_probability:.1f}%. Direction vs last week: {output.fomc_direction}
- 2-year yield: {output.yield_2y:.3f}% 10-year yield: {output.yield_10y:.3f}% 30-year yield: {output.yield_30y:.3f}%
- Yield curve: {output.yield_curve}. 10-year direction this week: {output.yield_10y_direction}

COMMODITIES & DOLLAR (Yfinance):

- WTI Crude Oil: {self.format_price(output.wti_oil.price)}, weekly change {self.format_percent(output.wti_oil.weekly_change)}, direction: {output.wti_oil.direction}
- Gold: {self.format_price(output.gold.price)}, weekly change {self.format_percent(output.gold.weekly_change)}, direction: {output.gold.direction}
- DXY (Dollar): {self.format_price(output.dxy.price)}, weekly change {self.format_percent(output.dxy.weekly_change)}, direction: {output.dxy.direction}

WEEK-AHEAD CALENDAR (TradingEconomics):

{self.render_calendar_events(output)}

KEY EARNINGS THIS WEEK (Earnings Whispers / TradingEconomics):

{self.render_key_earnings(output)}

CONFIRMED NEWS EVENTS (NewsData.io — Reuters/AP only):

{self.render_confirmed_news(output)}

MACRO BIAS: {output.macro_bias.value if output.macro_bias else "N/A"}

PRIMARY DRIVER THIS WEEK: {output.primary_driver}

CONFIDENCE: {output.confidence.value if output.confidence else "N/A"}

INVALIDATION: {output.invalidation}

Sources accessed: {prediction_date}
"""

    @classmethod
    def parse_md(cls, text: str, prediction_date: date | None = None) -> MacroOutput:
        """Inverse of ``render_md``."""
        pred = _date_from_md(text) or prediction_date
        if pred is None:
            raise ValueError("macro: could not determine prediction_date")
        fomc_raw = md.first(r"Next FOMC date:\s*([A-Za-z]+ \d+, \d{4})", text)
        next_fomc = None
        if fomc_raw:
            try:
                next_fomc = datetime.strptime(fomc_raw, "%B %d, %Y").date()
            except ValueError:
                next_fomc = None

        yields = re.search(
            r"2-year yield:\s*([\d.]+)%\s*10-year yield:\s*([\d.]+)%\s*30-year yield:\s*([\d.]+)%",
            text,
        )

        calendar = [
            CalendarEvent(
                date_label=m.group("date_label").strip(),
                name=_strip_md_link(m.group("name")),
                impact=m.group("impact").strip(),
                expected=m.group("expected").strip() or "N/A",
                previous=m.group("previous").strip() or "N/A",
                priority=0,
                source_url="",
            )
            for m in _CAL_RE.finditer(text)
        ]

        return MacroOutput(
            prediction_date=pred,
            fed_rate=md.first(r"Current Fed rate:\s*(.+)", text) or "",
            yield_2y=float(yields.group(1)) if yields else 0.0,
            yield_10y=float(yields.group(2)) if yields else 0.0,
            yield_30y=float(yields.group(3)) if yields else 0.0,
            dxy=_commodity(text, _COMMODITY_RE["dxy"]),
            wti_oil=_commodity(text, _COMMODITY_RE["wti_oil"]),
            gold=_commodity(text, _COMMODITY_RE["gold"]),
            macro_bias=MacroBias(md.norm_macro_bias(md.first(r"MACRO BIAS:\s*(.+)", text) or "")),
            primary_driver=(md.first(r"PRIMARY DRIVER THIS WEEK:\s*(.+)", text) or "").strip(),
            confidence=Confidence(md.norm_confidence(md.first(r"^CONFIDENCE:\s*([A-Za-z–—-]+)", text) or "")),
            invalidation=md.first(r"INVALIDATION:\s*(.+)", text) or "",
            next_fomc_date=next_fomc,
            hold_probability=float(md.first(r"Hold probability:\s*([\d.]+)%", text) or 0.0),
            cut_probability=float(md.first(r"Cut probability:\s*([\d.]+)%", text) or 0.0),
            fomc_direction=md.first(r"Direction vs last week:\s*(.+)", text) or "N/A",
            yield_curve=md.first(r"Yield curve:\s*([A-Za-z]+)", text) or "N/A",
            yield_10y_direction=md.first(r"10-year direction this week:\s*(\w+)", text) or "N/A",
            week_ahead_calendar=calendar,
            key_earnings=_bullets(text, "KEY EARNINGS"),
            confirmed_news=_bullets(text, "CONFIRMED NEWS"),
        )

    def save_md(self, output: MacroOutput, prediction_date: date) -> None:
        """Render MacroOutput to MD matching data/formats/macro_agent.md"""
        week = prediction_date.isocalendar()
        filename = f"macro_agent_W{week.week:02d}.md"
        out_dir = DATA_DIR / "macro"
        out_dir.mkdir(parents=True, exist_ok=True)

        content = f"""Macro Agent Output — Week of {self.report_week_label(prediction_date)} — Source: R4

FED & RATES (FRED & Yfinance):

- Current Fed rate: {output.fed_rate}
- Next FOMC date: {self.full_date_label(output.next_fomc_date)}. Hold probability: {output.hold_probability:.1f}%. Cut probability: {output.cut_probability:.1f}%. Direction vs last week: {output.fomc_direction}
- 2-year yield: {output.yield_2y:.3f}% 10-year yield: {output.yield_10y:.3f}% 30-year yield: {output.yield_30y:.3f}%
- Yield curve: {output.yield_curve}. 10-year direction this week: {output.yield_10y_direction}

COMMODITIES & DOLLAR (Yfinance):

- WTI Crude Oil: {self.format_price(output.wti_oil.price)}, weekly change {self.format_percent(output.wti_oil.weekly_change)}, direction: {output.wti_oil.direction}
- Gold: {self.format_price(output.gold.price)}, weekly change {self.format_percent(output.gold.weekly_change)}, direction: {output.gold.direction}
- DXY (Dollar): {self.format_price(output.dxy.price)}, weekly change {self.format_percent(output.dxy.weekly_change)}, direction: {output.dxy.direction}

WEEK-AHEAD CALENDAR (TradingEconomics):

{self.render_calendar_events(output)}

KEY EARNINGS THIS WEEK (Earnings Whispers / TradingEconomics): 

{self.render_key_earnings(output)}

CONFIRMED NEWS EVENTS (NewsData.io — Reuters/AP only): 

{self.render_confirmed_news(output)}

MACRO BIAS: {output.macro_bias.value if output.macro_bias else "N/A"}

PRIMARY DRIVER THIS WEEK: {output.primary_driver}

CONFIDENCE: {output.confidence.value if output.confidence else "N/A"}

INVALIDATION: {output.invalidation}

Sources accessed: {prediction_date}
"""
        (out_dir / filename).write_text(content, encoding="utf-8")


if __name__ == "__main__":
    prediction_date = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    agent = MacroAgent()
    output = agent.run(prediction_date)
    agent.save_json(output, prediction_date)
    agent.save_md(output, prediction_date)
    print("Saved to data/outputs/macro/ and data/macro/")