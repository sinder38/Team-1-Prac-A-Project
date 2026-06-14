"""
Macro Agent — fetches Fed rates, yields, commodities, and macro calendar data.

Usage:
    Add Api_key (either by .env file or by command)
    python backend/agents/macro/macro_agent.py 2026-06-16
"""
import json
import os
from datetime import date
from dataclasses import asdict
from pathlib import Path
import sys
import requests
import yfinance as yf
import pandas as pd
from dotenv import load_dotenv
from macro_event_data import (
    UPCOMING_EVENTS,
    CONFIRMED_NEWS,
    FOMC_MARKET_PRICING,
    KEY_EARNINGS,
)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base import BaseAgent
from agents.schemas import (
    CalendarEvent,
    CommodityData,
    Confidence,
    MacroBias,
    MacroOutput,
)

REPO_ROOT = Path(__file__).resolve().parents[3]

load_dotenv()


class MacroAgent(BaseAgent):
    agent_type = "macro"

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

    def fetch_fred(self, series: str, api_key: str) -> float | None:
        """Fetch latest observation from FRED API."""
        url = (
            "https://api.stlouisfed.org/fred/series/observations"
            f"?series_id={series}"
            f"&api_key={api_key}"
            "&file_type=json"
            "&sort_order=desc"
            "&limit=1"
        )
        try:
            data = requests.get(url).json()
            return float(data["observations"][0]["value"])
        except (requests.RequestException, KeyError, ValueError, IndexError) as e:
            print(f"Error fetching {series}: {e}")
            return None

    def fetch_fred_weekly_change(self, series: str, api_key: str) -> float:
        """Weekly change in percentage points for FRED series."""
        url = (
            "https://api.stlouisfed.org/fred/series/observations"
            f"?series_id={series}"
            f"&api_key={api_key}"
            "&file_type=json"
            "&sort_order=desc"
            "&limit=8"
        )
        try:
            data = requests.get(url).json()
            values = [
                float(obs["value"])
                for obs in data["observations"]
                if obs["value"] != "."
            ]
            if len(values) >= 7:
                return round(values[0] - values[5], 2)
            return 0.0
        except (requests.RequestException, KeyError, ValueError, IndexError) as e:
            print(f"Error fetching weekly change for {series}: {e}")
            return 0.0

    def get_fed_rate(self, api_key: str) -> str:
        """Get current Fed rate (lower and upper bound)."""
        low = self.fetch_fred("DFEDTARL", api_key)
        high = self.fetch_fred("DFEDTARU", api_key)
        if low is not None and high is not None:
            return f"{low:.2f}%-{high:.2f}%"
        return "N/A"

    def get_yields(self, api_key: str) -> dict:
        """Get Treasury yields: 2-year, 10-year, 30-year."""
        yield_2y = self.fetch_fred("DGS2", api_key)
        yield_10y = self.fetch_fred("DGS10", api_key)
        yield_30y = self.fetch_fred("DGS30", api_key)
        return {
            "2y": yield_2y if yield_2y is not None else 0.0,
            "10y": yield_10y if yield_10y is not None else 0.0,
            "30y": yield_30y if yield_30y is not None else 0.0,
        }

    def latest_price(self, ticker: str) -> float | None:
        """Get latest closing price for a ticker."""
        try:
            price = yf.Ticker(ticker).history(period="5d")["Close"].iloc[-1]
            return float(price) if pd.notna(price) else None
        except Exception as e:
            print(f"Error fetching price for {ticker}: {e}")
            return None

    def get_weekly_return(self, ticker: str) -> float:
        """Get weekly return for a single ticker (last close vs 5 trading days ago)."""
        try:
            raw = yf.download(ticker, period="1mo", interval="1d", auto_adjust=True)
            if raw is None or raw.empty:
                return 0.0
            data = raw["Close"]
            if isinstance(data, pd.Series):
                data = data.to_frame()

            s = data[ticker].dropna() if isinstance(data, pd.DataFrame) else data.dropna()

            if len(s) >= 6:
                # Last price vs 5 trading days ago
                change_pct = (s.iloc[-1] / s.iloc[-6] - 1) * 100
                return round(change_pct, 4)
            return 0.0
        except Exception as e:
            print(f"Error fetching weekly return for {ticker}: {e}")
            return 0.0

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
            price=round(price, 4) if price is not None else 0.0,
            weekly_change=weekly_change,
            direction=self.direction_from_change(
                weekly_change,
                positive=positive_direction,
                negative=negative_direction,
                flat=flat_direction,
            ),
        )

    def build_week_ahead_calendar(self) -> list[CalendarEvent]:
        """Convert configured event fixtures to schema objects for export."""
        return [
            CalendarEvent(
                date_label=event.date_label,
                name=event.name,
                impact=event.impact.title(),
                expected=event.expected,
                previous=event.previous,
            )
            for event in UPCOMING_EVENTS
        ]

    def build_primary_driver(self) -> str:
        """Describe the top-priority event as the report's primary driver."""
        if not UPCOMING_EVENTS:
            return "- No major scheduled events"

        primary_event = max(UPCOMING_EVENTS, key=lambda e: e.priority)
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
                "A materially more dovish-than-expected Fed decision or press "
                "conference that drives Treasury yields lower and increases "
                "expectations for Fed rate cuts would reverse the current "
                "cautious stance and support risk assets."
            )
        if macro_bias == MacroBias.HAWKISH:
            return (
                "A materially softer inflation or growth signal that pushes "
                "Treasury yields lower would invalidate the hawkish bias."
            )
        if macro_bias == MacroBias.DOVISH:
            return (
                "A materially stronger inflation or growth signal that pushes "
                "Treasury yields higher would invalidate the dovish bias."
            )
        return "Major events or significant shift in inflation expectations"

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
        if dxy_change > 1:
            score += 1
        elif dxy_change < -1:
            score -= 1

        # Front-end rates (2-year)
        if yield_2y_change > 0.15:
            score += 2
        elif yield_2y_change < -0.15:
            score -= 2

        # Long-end rates (10-year)
        if yield_10y_change > 0.10:
            score += 1
        elif yield_10y_change < -0.10:
            score -= 1

        # Gold (inverse relationship)
        if gold_change > 1:
            score -= 1
        elif gold_change < -1:
            score += 1

        # Oil
        if wti_change > 5:
            score += 1
        elif wti_change < -5:
            score -= 1

        # Determine bias based on score
        if score >= 3:
            bias = MacroBias.HAWKISH
        elif score <= -3:
            bias = MacroBias.DOVISH
        else:
            bias = MacroBias.NEUTRAL

        return bias, score

    def calculate_event_risk(self, events):
        """Calculate Event Risk."""
        score = 0

        for event in events:
            if event.impact == "HIGH":
                score += 3
            elif event.impact == "MEDIUM":
                score += 1

        return score

    def fetch_macro_data(self, prediction_date: date) -> MacroOutput:
        """
        Fetch Fed rate, Treasury yields, DXY, WTI, and Gold with weekly changes.
        Uses FRED API for rates/yields and yfinance for commodities.
        """
        api_key = os.getenv("FRED_API_KEY")

        if not api_key:
            raise ValueError("FRED_API_KEY environment variable is not set for macro")

        # Fed rate
        fed_rate = self.get_fed_rate(api_key)

        # Treasury yields (current levels)
        yields = self.get_yields(api_key)
        yield_2y = yields["2y"]
        yield_10y = yields["10y"]
        yield_30y = yields["30y"]

        # Treasury yield changes (weekly)
        yield_2y_change = self.fetch_fred_weekly_change("DGS2", api_key)
        yield_10y_change = self.fetch_fred_weekly_change("DGS10", api_key)

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
        if abs_score >= 4:
            confidence = Confidence.HIGH
        elif abs_score >= 2:
            confidence = Confidence.MEDIUM
        else:
            confidence = Confidence.LOW

        # Consider event risk score for bias and confidence
        event_risk_score = self.calculate_event_risk(UPCOMING_EVENTS)
        if event_risk_score >= 10:
            macro_bias = MacroBias.BINARY_RISK
            confidence = Confidence.MEDIUM

        primary_driver = self.build_primary_driver()
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
            next_fomc_date=FOMC_MARKET_PRICING.next_fomc_date,
            hold_probability=FOMC_MARKET_PRICING.hold_probability,
            cut_probability=FOMC_MARKET_PRICING.cut_probability,
            fomc_direction=FOMC_MARKET_PRICING.direction_vs_last_week,
            yield_curve=self.determine_yield_curve(yield_2y, yield_10y),
            yield_10y_direction=self.direction_from_change(yield_10y_change),
            week_ahead_calendar=self.build_week_ahead_calendar(),
            key_earnings=KEY_EARNINGS,
            confirmed_news=CONFIRMED_NEWS,
        )

    def run(self, prediction_date: date, **kwargs) -> MacroOutput:
        return self.fetch_macro_data(prediction_date)

    def save_json(self, output: MacroOutput, prediction_date: date) -> None:
        """Serialize output to data/outputs/macro/{YYYY-WNN}.json."""
        week = prediction_date.isocalendar()
        filename = f"{week.year}-W{week.week:02d}.json"
        out_dir = REPO_ROOT / "data" / "outputs" / self.agent_type
        out_dir.mkdir(parents=True, exist_ok=True)
        with open(out_dir / filename, "w", encoding="utf-8") as f:
            json.dump(asdict(output), f, indent=2, default=str)

    def render_calendar_events(self, output: MacroOutput) -> str:
        """Render week-ahead calendar rows."""
        if not output.week_ahead_calendar:
            return "- No high-impact macro calendar events configured."

        return "\n\n".join(
            (
                f"- {event.date_label}: {event.name} — Expected: "
                f"{event.expected}, Previous: {event.previous} — "
                f"IMPORTANCE: {event.impact}"
            )
            for event in output.week_ahead_calendar
        )

    def render_key_earnings(self, output: MacroOutput) -> str:
        """Render key earnings rows."""
        if not output.key_earnings:
            return "- No key earnings configured."

        return "\n\n".join(output.key_earnings)

    def render_confirmed_news(self, output: MacroOutput) -> str:
        """Render confirmed Reuters/AP news rows."""
        if not output.confirmed_news:
            return "- No confirmed Reuters/AP news events configured."

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

KEY EARNINGS THIS WEEK (Earnings Whispers):

{self.render_key_earnings(output)}

CONFIRMED NEWS EVENTS (Reuters / AP):

{self.render_confirmed_news(output)}

MACRO BIAS: {output.macro_bias.value if output.macro_bias else "N/A"}

PRIMARY DRIVER THIS WEEK: {output.primary_driver}

CONFIDENCE: {output.confidence.value if output.confidence else "N/A"}

INVALIDATION: {output.invalidation}

Sources accessed: {prediction_date}
"""

    def save_md(self, output: MacroOutput, prediction_date: date) -> None:
        """Render MacroOutput to MD matching data/formats/macro_agent.md"""
        week = prediction_date.isocalendar()
        filename = f"macro_agent_W{week.week:02d}.md"
        out_dir = REPO_ROOT / "data" / "macro"
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

KEY EARNINGS THIS WEEK (Earnings Whispers): 

{self.render_key_earnings(output)}

CONFIRMED NEWS EVENTS (Reuters / AP): 

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
