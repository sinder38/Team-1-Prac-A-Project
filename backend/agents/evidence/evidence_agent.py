"""Evidence Agent - generates a weekly R8 actuals report.

It saves the markdown as data/evidence/actuals_WXX.md.
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any, cast

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base import BaseAgent
from agents.io import FileSaver, week_stem
from agents.evidence.report import EvidenceReportRenderer
from agents.schemas import EvidenceOutput
from agents.evidence.data_sources import FredYieldProvider, YahooFinanceEvidenceProvider
from agents.evidence.models import (
    BITCOIN_SPEC,
    BONDS_SPEC,
    EM_DASH,
    GOLD_SPEC,
    INDEX_SPECS,
    OIL_SPEC,
    PROJECT_WEEK_OFFSET,
    SECTOR_SPECS,
    VIX_SPEC,
    EvidenceSnapshot,
    MarketMove,
    MarketSpec,
    SectorMove,
    YieldMove,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


class EvidenceAgent(BaseAgent[EvidenceOutput]):
    agent_type = "evidence"

    def __init__(
            self,
            data_root: Path | None = None,
            market_data_provider: Any | None = None,
            yield_data_provider: Any | None = None
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
        """Generate file names to link with technical charts"""
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
