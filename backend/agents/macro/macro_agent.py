"""
Macro Agent — fetches Fed rates, yields, commodities, and macro calendar data.

Usage:
    python agents/macro/macro_agent.py 2026-06-16
"""
import json
from datetime import date, timedelta
from dataclasses import asdict
from pathlib import Path
import sys
import requests
import yfinance as yf
import pandas as pd
from macro_event_data import UPCOMING_EVENTS, CONFIRMED_NEWS

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base import BaseAgent
from agents.schemas import MacroOutput, MacroBias, Confidence, CommodityData

REPO_ROOT = Path(__file__).resolve().parents[3]


class MacroAgent(BaseAgent):
    agent_type = "macro"

    def fetch_fred(self, series: str, api_key: str) -> float:
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

    def latest_price(self, ticker: str) -> float:
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
            data = yf.download(ticker, period="1mo", interval="1d", auto_adjust=True)["Close"]
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

    def fetch_commodity_data(self, ticker: str) -> CommodityData:
        """Fetch commodity price and weekly change."""
        price = self.latest_price(ticker)
        weekly_change = self.get_weekly_return(ticker)

        return CommodityData(
            price=round(price, 4) if price is not None else 0.0,
            weekly_change=weekly_change,
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
        api_key = "9fd88d0ad7a6d5a788ca32f72d96b58c"

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

        # Consider event risk for confidence
        event_risk_score = self.calculate_event_risk(UPCOMING_EVENTS)
        if event_risk_score >= 10:
            if confidence == Confidence.HIGH:
                confidence = Confidence.MEDIUM
            elif confidence == Confidence.MEDIUM:
                confidence = Confidence.LOW

        # Primary driver (biggest mover this week)
        if UPCOMING_EVENTS:
            primary_event = max(
                UPCOMING_EVENTS,
                key=lambda e: e.priority
            )
            primary_driver = primary_event.name
        else:
            primary_driver = "No major scheduled events"

        invalidation = "Major events or significant shift in inflation expectations"

        return MacroOutput(
            prediction_date=prediction_date,
            fed_rate=fed_rate,
            yield_2y=round(yield_2y, 2),
            yield_10y=round(yield_10y, 2),
            yield_30y=round(yield_30y, 2),
            dxy=dxy_data,
            wti_oil=wti_data,
            gold=gold_data,
            macro_bias=macro_bias,
            primary_driver=primary_driver,
            confidence=confidence,
            invalidation=invalidation,
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

    def save_md(self, output: MacroOutput, prediction_date: date) -> None:
        """Render MacroOutput to MD matching data/formats/macro_agent.md"""
        week = prediction_date.isocalendar()
        filename = f"macro_agent_{week.year}-W{week.week:02d}.md"
        out_dir = REPO_ROOT / "data" / "macro"
        out_dir.mkdir(parents=True, exist_ok=True)

        content = f"""Macro Agent Output — Week of {prediction_date}
FED & RATES:
 · Current Fed rate: {output.fed_rate}
 · 2-year yield: {output.yield_2y}%
 · 10-year yield: {output.yield_10y}%
 · 30-year yield: {output.yield_30y}%

COMMODITIES & DOLLAR:
 · WTI Crude Oil: {output.wti_oil.price}, weekly change: {output.wti_oil.weekly_change:+.4f}%
 · Gold: {output.gold.price}, weekly change: {output.gold.weekly_change:+.4f}%
 · DXY (Dollar): {output.dxy.price}, weekly change: {output.dxy.weekly_change:+.4f}%

CONFIRMED NEWS EVENTS (Reuters / AP): {CONFIRMED_NEWS}

MACRO BIAS: {output.macro_bias.value if output.macro_bias else "N/A"}
PRIMARY DRIVER THIS WEEK: {output.primary_driver}
CONFIDENCE: {output.confidence.value if output.confidence else "N/A"}
INVALIDATION: {output.invalidation}
"""
        (out_dir / filename).write_text(content, encoding="utf-8")


if __name__ == "__main__":
    prediction_date = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    agent = MacroAgent()
    output = agent.run(prediction_date)
    agent.export(output, prediction_date, fmt="json")
    agent.export(output, prediction_date, fmt="md")
    print("Saved to data/outputs/macro/ and data/macro/")
