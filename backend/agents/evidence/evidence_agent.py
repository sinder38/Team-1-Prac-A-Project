"""Evidence Agent - generates a weekly R8 actuals report.

To run locally:

cd backend
uv sync
uv run python -m playwright install chromium
uv run python agents/evidence/evidence_agent.py 2026-06-16

It saves the markdown as data/evidence/actuals_WXX.md and captures the two
Finviz evidence screenshots used by the R8 workflow when browser support is
available.
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
from agents.schemas import EvidenceOutput

REPO_ROOT = Path(__file__).resolve().parents[3]

EM_DASH: Final[str] = "\u2014"
PROJECT_WEEK_OFFSET: Final[int] = 20
FINVIZ_FUTURES_URL: Final[str] = "https://finviz.com/futures_performance?v=12"
FINVIZ_SECTORS_URL: Final[str] = "https://finviz.com/published_map?t=sec&st=w1&f=061926&i=sec_w1_230810247"


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
    performance_screenshot: str
    sector_screenshot: str
    technical_chart_links: list[tuple[str, str]]


class EvidenceMarketDataProvider(Protocol):
    def history(self, ticker: str, start: date, end: date) -> pd.Series:
        """Return daily close prices from start through end, inclusive."""
        ...


class ScreenshotProvider(Protocol):
    def capture(self, url: str, path: Path) -> None:
        """Capture url to path as a PNG image."""
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


class PlaywrightScreenshotProvider:
    """Capture Finviz pages when Playwright and Chromium are installed."""

    def capture(self, url: str, path: Path) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Screenshot capture requires Playwright. Install it with "
                "`python -m pip install playwright` and then run "
                "`python -m playwright install chromium`."
            ) from exc

        path.parent.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )
            try:
                page = browser.new_page(
                    viewport={"width": 1600, "height": 1200},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/121.0.0.0 Safari/537.36"
                    ),
                )
                page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                try:
                    page.wait_for_load_state("load", timeout=15_000)
                except Exception:
                    pass
                page.wait_for_timeout(3_000)
                page.screenshot(path=str(path), full_page=True)
            finally:
                browser.close()


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
        yield_data_provider: YieldDataProvider | None = None,
        screenshot_provider: ScreenshotProvider | None = None,
        capture_screenshots: bool = True,
        require_screenshots: bool = True,
    ):
        self._data_root = data_root or REPO_ROOT / "data"
        self._market_data = market_data_provider or YahooFinanceEvidenceProvider()
        self._yield_data = yield_data_provider or FredYieldProvider()
        self._screenshot_provider = screenshot_provider or PlaywrightScreenshotProvider()
        self._capture_screenshots = capture_screenshots
        self._require_screenshots = require_screenshots

    def run(self, prediction_date: date, **kwargs) -> EvidenceOutput:
        week = week_stem(prediction_date)
        self.capture_finviz_screenshots(prediction_date)
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
        performance_screenshot, sector_screenshot = self._screenshot_filenames(prediction_date)
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
            performance_screenshot=performance_screenshot,
            sector_screenshot=sector_screenshot,
            technical_chart_links=technical_chart_links,
        )

    def render_md(self, output: EvidenceOutput, prediction_date: date) -> str:
        return output.content

    def render_report(self, snapshot: EvidenceSnapshot) -> str:
        project_week = self._project_week_number(snapshot.prediction_date)
        available_sectors = [
            sector for sector in snapshot.sectors if sector.weekly_change is not None
        ]
        sector_rows = self._render_sector_rows(snapshot.sectors)
        best_sector_lines = self._render_sector_summary(available_sectors[:3])
        worst_sector_lines = self._render_sector_summary(list(reversed(available_sectors[-3:])))
        screenshot_rows = self._render_screenshot_rows(snapshot)
        source_lines = self._render_source_lines(snapshot)

        return f"""# Week {project_week:02d} Market Report ({snapshot.week_end.year})

**Week ended:** {self._format_full_date(snapshot.week_end)}  
**Days the market was open:** {snapshot.open_days}

This file lists how the main markets moved last week. **Closing value** = price at the end of Friday. **Weekly change** = up or down for the whole week.

---

## Main Stock Indexes (3 we track)

These are the big U.S. stock benchmarks we score each week.

| What it is | Short name | Price at Friday close | Up or down this week |
|------------|------------|----------------------|----------------------|
{self._render_index_rows(snapshot.indexes)}

**In plain words:** {self._plain_words_indexes(snapshot.indexes)}

---

## Other Important Markets

Gold, oil, bonds, fear gauge (VIX), and crypto.

| What it is | Friday close | Up or down this week |
|------------|--------------|----------------------|
| {snapshot.gold.spec.label} | {self._format_close(snapshot.gold)} | **{self._format_direction(snapshot.gold.weekly_change)}** |
| {snapshot.oil.spec.label} | {self._format_close(snapshot.oil)} | **{self._format_direction(snapshot.oil.weekly_change)}** |
| **10-Year interest rate** | {self._format_yield_close(snapshot.ten_year)} | **{self._format_yield_direction(snapshot.ten_year.weekly_change_points)}** |
| {snapshot.bonds.spec.label} | {self._format_close(snapshot.bonds)} | **{self._format_direction(snapshot.bonds.weekly_change)}** |
| {snapshot.vix.spec.label} | {self._format_close(snapshot.vix)} | **{self._format_direction(snapshot.vix.weekly_change)}** |
| {snapshot.bitcoin.spec.label} | {self._format_close(snapshot.bitcoin)} | **{self._format_direction(snapshot.bitcoin.weekly_change)}** |

**In plain words:** {self._plain_words_other_markets(snapshot)}

---

## 11 Parts of the Stock Market (S&P sectors)

Each row is one industry group in the S&P 500.

| Rank | Industry group | Up or down this week |
|------|----------------|----------------------|
{sector_rows}

### Best 3 this week
{best_sector_lines}

### Worst 3 this week
{worst_sector_lines}

**In plain words:** {self._plain_words_sectors(snapshot.sectors)}

---

## Charts & Screenshots

Saved in the **evidence** folder:

| What the picture shows | File name |
|------------------------|-----------|
{screenshot_rows}

## Where the numbers came from

{source_lines}
"""

    def capture_finviz_screenshots(self, prediction_date: date) -> tuple[Path, Path]:
        performance_filename, sector_filename = self._screenshot_filenames(prediction_date)
        evidence_dir = self._data_root / "evidence"
        targets = [
            (FINVIZ_FUTURES_URL, evidence_dir / performance_filename),
            (FINVIZ_SECTORS_URL, evidence_dir / sector_filename),
        ]

        if not self._capture_screenshots:
            return targets[0][1], targets[1][1]

        for url, path in targets:
            try:
                self._screenshot_provider.capture(url, path)
            except Exception as exc:
                message = (
                    f"Could not save required Finviz screenshot for {url} to {path}: {exc}"
                )
                if self._require_screenshots:
                    raise RuntimeError(message) from exc
                print(f"[evidence] screenshot warning: {message}", file=sys.stderr)
        return targets[0][1], targets[1][1]

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

    @staticmethod
    def _project_week_number(prediction_date: date) -> int:
        project_week = prediction_date.isocalendar().week - PROJECT_WEEK_OFFSET
        return project_week if project_week > 0 else prediction_date.isocalendar().week

    def _screenshot_filenames(self, prediction_date: date) -> tuple[str, str]:
        year = self._week_bounds(prediction_date)[1].year
        week = week_stem(prediction_date)
        return (
            f"finviz_1W_{year}_{week}.png",
            f"finviz_sectors_5D_{year}_{week}.png",
        )

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

    def _render_screenshot_rows(self, snapshot: EvidenceSnapshot) -> str:
        rows = [
            (
                "| 1-week performance (Finviz) | "
                f"[{snapshot.performance_screenshot}](./{snapshot.performance_screenshot}) |"
            ),
            (
                "| S&P 500 map by sector (Finviz) | "
                f"[{snapshot.sector_screenshot}](./{snapshot.sector_screenshot}) |"
            ),
        ]
        rows.extend(
            f"| {label} | [{path}]({path}) |"
            for label, path in snapshot.technical_chart_links
        )
        return "\n".join(rows)

    def _render_source_lines(self, snapshot: EvidenceSnapshot) -> str:
        sources = [
            "- Finviz futures performance screenshot for 1-week cross-market visual evidence",
            "- Finviz S&P 500 sector map screenshot for sector visual evidence",
            "- Yahoo Finance adjusted daily close data via yfinance for SPX (^GSPC), NDX (^NDX), IWM, Gold (GC=F), Oil (CL=F), TLT, VIX (^VIX), Bitcoin (BTC-USD), and sector ETFs",
            "- 10-year Treasury yield from FRED series DGS10",
            "- Sector ETF proxies: XLK, XLE, XLF, XLY, XLP, XLI, XLB, XLV, XLU, XLRE, XLC",
        ]
        if snapshot.technical_chart_links:
            sources.append(
                "- ProRealTime daily chart screenshots generated by the technical agent under data/charts"
            )
        sources.append(f"- Sources accessed: {self._format_full_date(date.today())}")
        return "\n".join(sources)

    @staticmethod
    def _format_full_date(value: date) -> str:
        return f"{value:%A}, {value:%B} {value.day}, {value.year}"

    def _render_index_rows(self, indexes: list[MarketMove]) -> str:
        return "\n".join(
            (
                f"| {move.spec.label} | {move.spec.short_name} | "
                f"{self._format_close(move)} | **{self._format_direction(move.weekly_change)}** |"
            )
            for move in indexes
        )

    def _render_sector_rows(self, sectors: list[SectorMove]) -> str:
        rows = []
        for rank, sector in enumerate(sectors, start=1):
            direction = self._format_direction(sector.weekly_change)
            if sector.weekly_change is not None and (rank <= 3 or rank > len(sectors) - 3):
                direction = f"**{direction}**"
            rows.append(f"| {rank} | {sector.spec.name} | {direction} |")
        return "\n".join(rows)

    def _render_sector_summary(self, sectors: list[SectorMove]) -> str:
        if not sectors:
            return "No sector ETF data was available from Yahoo Finance for this completed week."
        return "\n".join(
            (
                f"{rank}. **{sector.spec.name}** {EM_DASH} "
                f"{self._format_direction_sentence(sector.weekly_change)}. "
                f"Move based on {sector.spec.description} via {sector.spec.ticker}."
            )
            for rank, sector in enumerate(sectors, start=1)
        )

    @staticmethod
    def _format_direction(value: float | None) -> str:
        if value is None:
            return "N/A"
        if value > 0:
            return f"Up {abs(value):.2f}%"
        if value < 0:
            return f"Down {abs(value):.2f}%"
        return "Flat 0.00%"

    @staticmethod
    def _format_direction_sentence(value: float | None) -> str:
        if value is None:
            return "N/A"
        if value > 0:
            return f"up {abs(value):.2f}%"
        if value < 0:
            return f"down {abs(value):.2f}%"
        return "flat 0.00%"

    @staticmethod
    def _format_yield_direction(change_points: float | None) -> str:
        if change_points is None:
            return "N/A"
        if abs(change_points) < 0.01:
            return "Flat (less than 0.01 points)"
        direction = "Slightly higher" if change_points > 0 else "Slightly lower"
        return f"{direction} (about {abs(change_points):.2f} points)"

    @staticmethod
    def _format_close(move: MarketMove) -> str:
        if move.close is None:
            return "N/A"
        if move.spec.close_kind == "gold":
            return f"${move.close:,.0f} per ounce"
        if move.spec.close_kind == "oil":
            return f"${move.close:,.2f} per barrel"
        if move.spec.close_kind == "bitcoin":
            return f"${move.close:,.0f}"
        if move.spec.close_kind == "vix":
            return f"{move.close:,.2f}"
        return f"{move.close:,.2f}"

    @staticmethod
    def _format_yield_close(move: YieldMove) -> str:
        if move.close is None:
            return "N/A"
        return f"{move.close:.2f}%"

    def _plain_words_indexes(self, indexes: list[MarketMove]) -> str:
        available = [move for move in indexes if move.weekly_change is not None]
        if not available:
            return "Yahoo Finance index table data was not available for this completed week. The saved Finviz 1-week screenshot is the visual evidence source."

        up_count = sum(1 for move in available if move.weekly_change and move.weekly_change > 0)
        down_count = sum(1 for move in available if move.weekly_change and move.weekly_change < 0)
        best = max(available, key=lambda move: move.weekly_change or 0.0)
        worst = min(available, key=lambda move: move.weekly_change or 0.0)

        if up_count == len(available):
            lead = f"All {len(available)} available index readings finished higher."
        elif down_count == len(available):
            lead = f"All {len(available)} available index readings finished lower."
        else:
            lead = f"{up_count} of {len(available)} available index readings rose and {down_count} fell."

        return (
            f"{lead} {best.spec.short_name} led with a "
            f"{self._format_direction_sentence(best.weekly_change)} move, while "
            f"{worst.spec.short_name} was the weakest at "
            f"{self._format_direction_sentence(worst.weekly_change)}."
        )

    def _plain_words_other_markets(self, snapshot: EvidenceSnapshot) -> str:
        if snapshot.vix.weekly_change is None:
            fear = "was unavailable"
        else:
            fear = "eased" if snapshot.vix.weekly_change < 0 else "rose"
        oil_direction = self._format_direction_sentence(snapshot.oil.weekly_change)
        bitcoin_direction = self._format_direction_sentence(snapshot.bitcoin.weekly_change)
        bond_direction = self._format_direction_sentence(snapshot.bonds.weekly_change)
        if snapshot.ten_year.weekly_change_points is None:
            yield_direction = "was unavailable"
        elif abs(snapshot.ten_year.weekly_change_points) < 0.01:
            yield_direction = "was little changed"
        elif snapshot.ten_year.weekly_change_points < 0:
            yield_direction = "edged down"
        else:
            yield_direction = "edged up"

        return (
            f"Fear {fear} as VIX moved {self._format_direction_sentence(snapshot.vix.weekly_change)}. "
            f"Oil was {oil_direction}, Bitcoin was {bitcoin_direction}, and bonds were "
            f"{bond_direction} as the 10-year yield {yield_direction}."
        )

    def _plain_words_sectors(self, sectors: list[SectorMove]) -> str:
        available = [sector for sector in sectors if sector.weekly_change is not None]
        if not available:
            return "Yahoo Finance sector ETF table data was not available for this completed week. The saved Finviz sector map screenshot is the visual evidence source."

        positive_count = sum(1 for sector in available if sector.weekly_change and sector.weekly_change > 0)
        best = available[0]
        worst = available[-1]
        breadth = (
            "a broad rally"
            if positive_count >= 8
            else "a mixed market"
            if positive_count >= 4
            else "a defensive or weak tape"
        )
        return (
            f"Sector breadth showed {breadth}: {positive_count} of {len(available)} available sectors finished green. "
            f"{best.spec.name} led at {self._format_direction_sentence(best.weekly_change)}, "
            f"while {worst.spec.name} lagged at {self._format_direction_sentence(worst.weekly_change)}."
        )


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