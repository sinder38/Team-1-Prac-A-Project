"""Evidence chart capture helpers (Finviz-style visuals from snapshot data)."""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from agents.evidence.generate_charts import EvidenceChartRenderer, render_evidence_charts
from agents.io import week_stem

if TYPE_CHECKING:
    from agents.evidence.models import EvidenceSnapshot


class ChartProvider(Protocol):
    def generate_evidence_charts(
        self,
        snapshot: EvidenceSnapshot,
        performance_path: Path,
        sector_path: Path,
    ) -> tuple[Path, Path]:
        """Generate performance and sector charts at the given paths."""
        ...


def screenshot_filenames(prediction_date: date) -> tuple[str, str]:
    week_start = prediction_date - timedelta(days=prediction_date.weekday())
    year = (week_start + timedelta(days=4)).year
    week = week_stem(prediction_date)
    return (
        f"finviz_1W_{year}_{week}.png",
        f"finviz_sectors_5D_{year}_{week}.png",
    )


class EvidenceChartCapturer:
    """Render weekly evidence charts from a fetched evidence snapshot."""

    def __init__(
        self,
        data_root: Path,
        chart_renderer: EvidenceChartRenderer | None = None,
        chart_provider: ChartProvider | None = None,
        require_charts: bool = True,
    ):
        self._data_root = data_root
        self._chart_renderer = chart_renderer
        self._chart_provider = chart_provider
        self._require_charts = require_charts

    def generate_evidence_charts(
        self,
        snapshot: EvidenceSnapshot,
        performance_path: Path,
        sector_path: Path,
    ) -> tuple[Path, Path]:
        try:
            if self._chart_provider is not None:
                return self._chart_provider.generate_evidence_charts(
                    snapshot,
                    performance_path,
                    sector_path,
                )
            return render_evidence_charts(
                week_start=snapshot.week_start,
                week_end=snapshot.week_end,
                performance_rows=snapshot.performance_chart,
                sector_rows=[
                    (sector.spec.name, sector.weekly_change, sector.spec.ticker)
                    for sector in snapshot.sectors
                ],
                performance_path=performance_path,
                sector_path=sector_path,
                chart_renderer=self._chart_renderer,
            )
        except Exception as exc:
            message = (
                "Could not save required evidence charts for "
                f"{performance_path} and {sector_path}: {exc}"
            )
            if self._require_charts:
                raise RuntimeError(message) from exc
            print(f"[evidence] chart warning: {message}", file=sys.stderr)
            return performance_path, sector_path