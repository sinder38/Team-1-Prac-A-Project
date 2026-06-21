"""Evidence Agent - generates a weekly R8 actuals report.

It saves the markdown as data/evidence/actuals_WXX.md.
capture is an explicit separate step; the report keeps Markdown table links to
the expected PNG filenames without embedding or creating those images.
"""

from __future__ import annotations

import sys
from io import StringIO
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Final, Protocol, cast

import pandas as pd
import requests
import yfinance as yf

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base import BaseAgent
from agents.io import FileSaver, week_stem
from agents.evidence.report import EvidenceReportRenderer
from agents.schemas import EvidenceOutput

REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class MarketSpec:
    label: str
    short_name: str
    ticker: str
    close_kind: str


@dataclass(frozen=True)
class SectorSpec:
    name: str
    ticker: str
    description: str


@dataclass(frozen=True)
class MarketMove:
    spec: MarketSpec
    close: float | None
    weekly_change: float | None
    error: str | None = None


@dataclass(frozen=True)
class YieldMove:
    close: float | None
    weekly_change_points: float | None
    error: str | None = None


@dataclass(frozen=True)
class SectorMove:
    spec: SectorSpec
    weekly_change: float | None
    error: str | None = None


@dataclass(frozen=True)
class EvidenceSnapshot:
    prediction_date: date
    week_start: date
    week_end: date
    last_market_date: date
    open_days: int
    indexes: list[MarketMove]
    gold: MarketMove
    oil: MarketMove
    ten_year: YieldMove
    bonds: MarketMove
    vix: MarketMove
    bitcoin: MarketMove
    sectors: list[SectorMove]
    technical_chart_links: list[tuple[str, str]]


class EvidenceMarketDataProvider(Protocol):
    def history(self, ticker: str, start: date, end: date) -> pd.Series:
        """Return daily close prices from start through end, inclusive."""
        ...


class YieldDataProvider(Protocol):
    def history(self, series_id: str, start: date, end: date) -> pd.Series:
        """Return daily yield values from start through end, inclusive."""
        ...


class YahooFinanceEvidenceProvider:
    """Small adapter around yfinance so tests can inject deterministic data."""

    def history(self, ticker: str, start: date, end: date) -> pd.Series:
        raw = yf.download(
            ticker,
            start=start.isoformat(),
            end=(end + timedelta(days=1)).isoformat(),
            progress=False,
            auto_adjust=True,
        )
        if raw is None or raw.empty:
            raise ValueError(f"No Yahoo Finance data returned for {ticker}")

        close = self._close_column(raw, ticker)
        close = pd.Series(
            close.to_numpy(),
            index=pd.DatetimeIndex(pd.to_datetime(close.index)).tz_localize(None),
            name=close.name,
        )
        close = cast(pd.Series, close.dropna().sort_index())
        if close.empty:
            raise ValueError(f"No close prices returned for {ticker}")
        return close

    @staticmethod
    def _close_column(raw: pd.DataFrame, ticker: str) -> pd.Series:
        if isinstance(raw.columns, pd.MultiIndex):
            if "Close" in raw.columns.get_level_values(0):
                close = raw["Close"]
            elif "Close" in raw.columns.get_level_values(-1):
                close = raw.xs("Close", axis=1, level=-1)
            else:
                raise ValueError(f"No close column returned for {ticker}")
            if isinstance(close, pd.DataFrame):
                if ticker in close.columns:
                    return cast(pd.Series, close[ticker])
                return cast(pd.Series, close.iloc[:, 0])
            return cast(pd.Series, close)

        if "Close" not in raw.columns:
            raise ValueError(f"No close column returned for {ticker}")
        close = raw["Close"]
        if isinstance(close, pd.DataFrame):
            return cast(pd.Series, close.iloc[:, 0])
        return cast(pd.Series, close)


class FredYieldProvider:
    """Fetch Treasury yields from FRED's CSV endpoint without requiring an API key."""

    _url: Final[str] = "https://fred.stlouisfed.org/graph/fredgraph.csv"

    def history(self, series_id: str, start: date, end: date) -> pd.Series:
        response = requests.get(
            self._url,
            params={"id": series_id},
            timeout=30,
        )
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text))
        if "observation_date" not in df.columns or series_id not in df.columns:
            raise ValueError(f"FRED response missing {series_id} data")

        raw_values = cast(pd.Series, df[series_id])
        values = cast(pd.Series, pd.to_numeric(raw_values, errors="coerce"))
        raw_dates = cast(pd.Series, df["observation_date"])
        dates = pd.DatetimeIndex(pd.to_datetime(raw_dates))
        series = pd.Series(values.to_numpy(), index=dates)
        series = cast(pd.Series, series.dropna().sort_index())
        index = pd.DatetimeIndex(series.index)
        filtered = [
            (item, float(value))
            for item, value in zip(index, series.to_numpy())
            if start <= item.date() <= end
        ]
        if not filtered:
            raise ValueError(f"No FRED {series_id} observations returned")
        return pd.Series(
            [value for _, value in filtered],
            index=pd.DatetimeIndex([item for item, _ in filtered]),
        )

INDEX_SPECS: Final[list[MarketSpec]] = [
    MarketSpec("S&P 500 \u2014 large U.S. companies", "SPX", "^GSPC", "index"),
    MarketSpec("Nasdaq 100 \u2014 mostly tech", "NDX", "^NDX", "index"),
    MarketSpec("Russell 2000 \u2014 smaller companies", "IWM", "IWM", "etf"),
]

GOLD_SPEC: Final[MarketSpec] = MarketSpec("**Gold**", "Gold", "GC=F", "gold")
OIL_SPEC: Final[MarketSpec] = MarketSpec("**Oil** (U.S. crude)", "Oil", "CL=F", "oil")
BONDS_SPEC: Final[MarketSpec] = MarketSpec("**Bonds** (TLT fund)", "TLT", "TLT", "etf")
VIX_SPEC: Final[MarketSpec] = MarketSpec(
    "**VIX** (how scared traders are; lower = calmer)", "VIX", "^VIX", "vix"
)
BITCOIN_SPEC: Final[MarketSpec] = MarketSpec("**Bitcoin**", "Bitcoin", "BTC-USD", "bitcoin")

SECTOR_SPECS: Final[list[SectorSpec]] = [
    SectorSpec("Technology", "XLK", "software, chips, and hardware"),
    SectorSpec("Energy (oil & gas companies)", "XLE", "oil and gas producers"),
    SectorSpec("Financials (banks, insurance)", "XLF", "banks, brokers, and insurers"),
    SectorSpec("Consumer discretionary (cars, hotels, shopping)", "XLY", "consumer spending-sensitive stocks"),
    SectorSpec("Consumer staples (food, toothpaste, etc.)", "XLP", "defensive food and household products"),
    SectorSpec("Industrials", "XLI", "manufacturers, transport, and machinery"),
    SectorSpec("Materials (chemicals, metals, etc.)", "XLB", "chemicals, metals, and industrial inputs"),
    SectorSpec("Health care", "XLV", "health care and pharmaceuticals"),
    SectorSpec("Utilities (power, water)", "XLU", "regulated power and water utilities"),
    SectorSpec("Real estate", "XLRE", "property and REIT stocks"),
    SectorSpec("Communication (phones, media, ads)", "XLC", "telecom, media, and internet platforms"),
]


class EvidenceAgent(BaseAgent[EvidenceOutput]):
    agent_type = "evidence"

    def __init__(
        self,
        data_root: Path | None = None,
        market_data_provider: EvidenceMarketDataProvider | None = None,
        yield_data_provider: YieldDataProvider | None = None
    ):
        self._data_root = data_root or REPO_ROOT / "data"
        self._market_data = market_data_provider or YahooFinanceEvidenceProvider()
        self._yield_data = yield_data_provider or FredYieldProvider()
        self._report_renderer = EvidenceReportRenderer()

    def run(self, prediction_date: date, **kwargs) -> EvidenceOutput:
        return self.generate_report(prediction_date)

    def generate_report(self, prediction_date: date) -> EvidenceOutput:
        """Generate the Markdown-backed evidence output without taking screenshots."""
        week = week_stem(prediction_date)
        snapshot = self.fetch_snapshot(prediction_date)
        content = self.render_report(snapshot)
        return EvidenceOutput(
            prediction_date=prediction_date,
            week=week,
            content=content,
        )

    def fetch_snapshot(self, prediction_date: date) -> EvidenceSnapshot:
        week_start, week_end = self._week_bounds(prediction_date)
        fetch_start = week_start - timedelta(days=10)
        technical_chart_links = self._technical_chart_links(prediction_date)

        index_moves = [self._market_move(spec, fetch_start, week_start, week_end) for spec in INDEX_SPECS]
        open_dates = self._market_open_dates(fetch_start, week_start, week_end)

        sectors = [
            SectorMove(spec=spec, weekly_change=self._weekly_change_pct(spec.ticker, fetch_start, week_start, week_end))
            for spec in SECTOR_SPECS
        ]
        sectors.sort(
            key=lambda item: item.weekly_change if item.weekly_change is not None else float("-inf"),
            reverse=True,
        )

        ten_year = self._yield_move(fetch_start, week_start, week_end)

        return EvidenceSnapshot(
            prediction_date=prediction_date,
            week_start=week_start,
            week_end=week_end,
            last_market_date=open_dates[-1],
            open_days=len(open_dates),
            indexes=index_moves,
            gold=self._market_move(GOLD_SPEC, fetch_start, week_start, week_end),
            oil=self._market_move(OIL_SPEC, fetch_start, week_start, week_end),
            ten_year=ten_year,
            bonds=self._market_move(BONDS_SPEC, fetch_start, week_start, week_end),
            vix=self._market_move(VIX_SPEC, fetch_start, week_start, week_end),
            bitcoin=self._market_move(BITCOIN_SPEC, fetch_start, week_start, week_end),
            sectors=sectors,
            technical_chart_links=technical_chart_links,
        )

    def render_md(self, output: EvidenceOutput, prediction_date: date) -> str:
        return output.content

    def render_report(self, snapshot: EvidenceSnapshot) -> str:
        return self._report_renderer.render(snapshot)


    def _market_move(
        self,
        spec: MarketSpec,
        fetch_start: date,
        week_start: date,
        week_end: date,
    ) -> MarketMove:
        try:
            series = self._market_data.history(spec.ticker, fetch_start, week_end)
            previous, current, _ = self._weekly_prices(series, week_start, week_end)
            return MarketMove(
                spec=spec,
                close=current,
                weekly_change=(current / previous - 1.0) * 100.0,
            )
        except Exception as exc:
            return MarketMove(spec=spec, close=None, weekly_change=None, error=str(exc))

    def _yield_move(self, fetch_start: date, week_start: date, week_end: date) -> YieldMove:
        try:
            ten_year_series = self._yield_data.history("DGS10", fetch_start, week_end)
            previous_yield, current_yield, _ = self._weekly_prices(
                ten_year_series, week_start, week_end
            )
            return YieldMove(
                close=current_yield,
                weekly_change_points=current_yield - previous_yield,
            )
        except Exception as exc:
            return YieldMove(close=None, weekly_change_points=None, error=str(exc))

    def _weekly_change_pct(
        self,
        ticker: str,
        fetch_start: date,
        week_start: date,
        week_end: date,
    ) -> float | None:
        try:
            series = self._market_data.history(ticker, fetch_start, week_end)
            previous, current, _ = self._weekly_prices(series, week_start, week_end)
            return (current / previous - 1.0) * 100.0
        except Exception:
            return None

    def _market_open_dates(
        self,
        fetch_start: date,
        week_start: date,
        week_end: date,
    ) -> list[date]:
        try:
            spx_series = self._market_data.history(INDEX_SPECS[0].ticker, fetch_start, week_end)
            _, _, open_dates = self._weekly_prices(spx_series, week_start, week_end)
            return open_dates
        except Exception:
            return [
                week_start + timedelta(days=offset)
                for offset in range((week_end - week_start).days + 1)
                if (week_start + timedelta(days=offset)).weekday() <= 4
            ]

    @staticmethod
    def _weekly_prices(series: pd.Series, week_start: date, week_end: date) -> tuple[float, float, list[date]]:
        cleaned = cast(pd.Series, series.dropna().sort_index())
        index = pd.DatetimeIndex(pd.to_datetime(cleaned.index)).tz_localize(None)
        cleaned = pd.Series(cleaned.to_numpy(), index=index, name=cleaned.name)
        index = pd.DatetimeIndex(cleaned.index)
        values = [
            (item.date(), float(value))
            for item, value in zip(index, cleaned.to_numpy())
            if item.weekday() <= 4
        ]

        prior = [value for day, value in values if day < week_start]
        current_week = [
            (day, value) for day, value in values if week_start <= day <= week_end
        ]

        if not prior:
            raise ValueError(f"No prior close available before {week_start}")
        if not current_week:
            raise ValueError(f"No market closes available for {week_start} to {week_end}")

        open_dates = [day for day, _ in current_week]
        return prior[-1], current_week[-1][1], open_dates

    @staticmethod
    def _week_bounds(prediction_date: date) -> tuple[date, date]:
        week_start = prediction_date - timedelta(days=prediction_date.weekday())
        week_end = week_start + timedelta(days=4)
        return week_start, week_end

    def _technical_chart_links(self, prediction_date: date) -> list[tuple[str, str]]:
        charts_dir = self._data_root / "charts"
        week = week_stem(prediction_date)
        year = self._week_bounds(prediction_date)[1].year
        chart_specs = [
            ("S&P 500 daily chart (ProRealTime)", "SPX"),
            ("Nasdaq 100 daily chart (ProRealTime)", "NDX"),
            ("Russell 2000 daily chart (ProRealTime)", "IWM"),
        ]
        links: list[tuple[str, str]] = []
        for label, symbol in chart_specs:
            candidates = [
                charts_dir / f"technical_{symbol}_{year}-{week}.png",
                charts_dir / f"technical_{symbol}_{year}_{week}.png",
                charts_dir / f"technical_{symbol}_{week}.png",
            ]
            for path in candidates:
                if path.exists():
                    links.append((label, f"../charts/{path.name}"))
                    break
        return links

if __name__ == "__main__":
    prediction_date = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    agent = EvidenceAgent()
    output = agent.run(prediction_date)

    FileSaver.for_agent(agent.agent_type).save(
        agent.render_json(output, prediction_date), f"{week_stem(prediction_date)}.json"
    )
    FileSaver(REPO_ROOT / "data" / agent.agent_type).save(
        agent.render_md(output, prediction_date),
        f"actuals_{week_stem(prediction_date)}.md",
    )
    print("Saved to data/outputs/evidence/ and data/evidence/")