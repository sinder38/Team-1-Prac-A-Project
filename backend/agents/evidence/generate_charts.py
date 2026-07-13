"""Render Finviz-style evidence charts from an evidence agent snapshot."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Final, Protocol

import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors as mcolors

FINVIZ_POSITIVE: Final[str] = "#3d8f3d"
FINVIZ_NEGATIVE: Final[str] = "#b33a3a"
FINVIZ_NEUTRAL: Final[str] = "#4a4a4a"
FINVIZ_BG: Final[str] = "#1a1a2e"
FINVIZ_PANEL: Final[str] = "#16213e"
FINVIZ_TEXT: Final[str] = "#e8e8e8"


class EvidenceChartRenderer(Protocol):
    def render_performance_chart(
            self,
            path: Path,
            instruments: list[tuple[str, float | None]],
            week_start: date,
            week_end: date,
    ) -> None:
        """Render a 1-week performance bar chart to path."""

    def render_sector_heatmap(
            self,
            path: Path,
            sectors: list[tuple[str, float | None, str]],
            week_start: date,
            week_end: date,
    ) -> None:
        """Render a sector performance heatmap to path."""


def performance_color(value: float | None) -> str:
    if value is None:
        return FINVIZ_NEUTRAL
    if value > 0:
        return FINVIZ_POSITIVE
    if value < 0:
        return FINVIZ_NEGATIVE
    return FINVIZ_NEUTRAL


def _format_week_range(week_start: date, week_end: date) -> str:
    return f"{week_start:%b %d} – {week_end:%b %d, %Y}"


def has_chartable_sector_data(
        sectors: list[tuple[str, float | None, str]],
) -> bool:
    return any(change is not None for _, change, _ in sectors)


class MatplotlibEvidenceChartRenderer:
    """Render Finviz-inspired charts with matplotlib."""

    def render_performance_chart(
            self,
            path: Path,
            instruments: list[tuple[str, float | None]],
            week_start: date,
            week_end: date,
    ) -> None:
        available = sorted(
            [(label, value) for label, value in instruments if value is not None],
            key=lambda item: item[1],
            reverse=True,
        )
        if not available:
            raise ValueError("No performance data available to chart")

        labels = [label for label, _ in available]
        values = [value for _, value in available]
        bar_lengths = [abs(value) for value in values]
        colors = [performance_color(value) for value in values]

        label_width = max(len(label) for label in labels)
        fig_width = 12 + label_width * 0.04
        fig, ax = plt.subplots(figsize=(fig_width, max(6, len(available) * 0.45 + 1.5)))
        fig.patch.set_facecolor(FINVIZ_BG)
        ax.set_facecolor(FINVIZ_PANEL)

        y_positions = np.arange(len(labels))
        ax.barh(y_positions, bar_lengths, left=0, color=colors, height=0.7, edgecolor="#0f0f1a")
        ax.invert_yaxis()

        max_length = max(bar_lengths) if bar_lengths else 1.0
        padding = max(max_length * 0.08, 0.2)
        ax.set_xlim(0, max_length + padding * 2)
        ax.set_yticks(y_positions)
        ax.set_yticklabels(labels, color=FINVIZ_TEXT, fontsize=10)

        for index, (value, length) in enumerate(zip(values, bar_lengths, strict=False)):
            ax.text(
                length + padding * 0.15,
                index,
                f"{value:+.2f}%",
                va="center",
                ha="left",
                color=FINVIZ_TEXT,
                fontsize=9,
                fontweight="bold",
            )

        ax.set_xlabel("Weekly % change vs prior week close", color=FINVIZ_TEXT)
        ax.set_title(
            f"1-Week Market Performance ({_format_week_range(week_start, week_end)})",
            color=FINVIZ_TEXT,
            fontsize=14,
            pad=12,
        )
        ax.tick_params(axis="x", colors=FINVIZ_TEXT)
        ax.tick_params(axis="y", length=0)
        for spine in ax.spines.values():
            spine.set_color("#333355")

        fig.tight_layout()
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=150, facecolor=fig.get_facecolor(), bbox_inches="tight")
        plt.close(fig)

    def render_sector_heatmap(
            self,
            path: Path,
            sectors: list[tuple[str, float | None, str]],
            week_start: date,
            week_end: date,
    ) -> bool:
        available = [
            (name, change, ticker)
            for name, change, ticker in sectors
            if change is not None
        ]
        if not available:
            return False

        available.sort(key=lambda item: item[1], reverse=True)

        norm = mcolors.TwoSlopeNorm(vmin=-3.0, vcenter=0.0, vmax=3.0)
        cmap = mcolors.LinearSegmentedColormap.from_list(
            "finviz",
            [FINVIZ_NEGATIVE, "#2a2a3a", FINVIZ_POSITIVE],
        )

        columns = 4
        rows = (len(available) + columns - 1) // columns
        fig, ax = plt.subplots(figsize=(12, 2.2 + rows * 1.55))
        fig.patch.set_facecolor(FINVIZ_BG)
        ax.set_facecolor(FINVIZ_BG)
        ax.set_xlim(0, columns)
        ax.set_ylim(0, rows)
        ax.axis("off")

        text_outline = [pe.withStroke(linewidth=2.5, foreground="#000000")]

        for index, (name, change, ticker) in enumerate(available):
            row = index // columns
            col = index % columns
            x = col
            y = rows - row - 1

            facecolor = cmap(norm(change))
            rect = mpatches.Rectangle(
                (x + 0.04, y + 0.08),
                0.92,
                0.84,
                facecolor=facecolor,
                edgecolor="#0f0f1a",
                linewidth=1.5,
            )
            ax.add_patch(rect)

            short_name = name.split(" (")[0]
            ax.text(
                x + 0.5,
                y + 0.58,
                ticker,
                ha="center",
                va="center",
                color=FINVIZ_TEXT,
                fontsize=13,
                fontweight="bold",
                path_effects=text_outline,
            )
            ax.text(
                x + 0.5,
                y + 0.30,
                f"{change:+.2f}%",
                ha="center",
                va="center",
                color=FINVIZ_TEXT,
                fontsize=11,
                fontweight="bold",
                path_effects=text_outline,
            )
            ax.text(
                x + 0.5,
                y + 0.14,
                short_name,
                ha="center",
                va="center",
                color="#d0d0d0",
                fontsize=7,
                path_effects=text_outline,
            )

        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, fraction=0.025, pad=0.02)
        cbar.set_label("Weekly % change vs prior week close", color=FINVIZ_TEXT)
        cbar.ax.yaxis.set_tick_params(color=FINVIZ_TEXT)
        plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color=FINVIZ_TEXT)

        ax.set_title(
            f"S&P 500 Sector Heatmap ({_format_week_range(week_start, week_end)})",
            color=FINVIZ_TEXT,
            fontsize=14,
            pad=12,
        )

        fig.tight_layout()
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=150, facecolor=fig.get_facecolor(), bbox_inches="tight")
        plt.close(fig)
        return True


def render_evidence_charts(
        *,
        week_start: date,
        week_end: date,
        performance_rows: list[tuple[str, float | None]],
        sector_rows: list[tuple[str, float | None, str]],
        performance_path: Path,
        sector_path: Path,
        chart_renderer: EvidenceChartRenderer | None = None,
) -> tuple[Path, Path | None]:
    """Render chart PNGs from pre-fetched weekly performance rows."""
    renderer = chart_renderer or MatplotlibEvidenceChartRenderer()
    renderer.render_performance_chart(performance_path, performance_rows, week_start, week_end)
    sector_written = renderer.render_sector_heatmap(
        sector_path, sector_rows, week_start, week_end
    )
    return performance_path, sector_path if sector_written else None
