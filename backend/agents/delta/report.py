"""Render Delta Engine results as the weekly Markdown deliverable."""

from agents.delta.models import (
    ASSET_LABELS,
    DeltaReport,
    DeltaRow,
    SECTOR_ASSETS,
    WeekAccuracy,
    WeightAdjustment,
)
from agents.delta.parsing import plain_week
from agents.delta.scoring import join_assets, sector_coverage


def render_delta_markdown(report: DeltaReport) -> str:
    week = plain_week(report.prediction_week)
    lines = [
        f"# delta_{week}.md",
        "",
        "Role: Delta Engine / Calibration",
        "Status: Generated from a locked prediction and completed actuals",
        "",
        "## Files compared",
        "",
        f"- Locked prediction: {report.prediction_week}",
        f"- Completed actuals: {report.actuals_week}",
        "",
        "## Current-week score",
        "",
        (
            "| Asset | Predicted direction | Predicted range | Confidence | "
            "Actual move | Actual direction | Direction correct? | "
            "Range hit? | Range error |"
        ),
        "| --- | --- | ---: | --- | ---: | --- | --- | --- | ---: |",
        *[_render_score_row(row) for row in report.rows],
        "",
        "## Current-week summary",
        "",
        (
            f"- Direction accuracy: {report.direction_correct_count} / "
            f"{len(report.rows)}"
        ),
        (
            f"- Range accuracy: {report.range_hit_count} / "
            f"{report.ranged_asset_count}"
        ),
        f"- Average range error: {report.average_error_percent:.2f}%",
        (
            f"- Sector coverage: {sector_coverage(report.rows)} / "
            f"{len(SECTOR_ASSETS)}"
        ),
        "",
        "## Cumulative accuracy",
        "",
        (
            "This history only uses locked predictions with the matching "
            "completed actuals. Missing weeks are not estimated."
        ),
        "",
        (
            "| Prediction | Actuals | Assets scored | Direction accuracy | "
            "Range accuracy | Average range error |"
        ),
        "| --- | --- | ---: | ---: | ---: | ---: |",
        *[_render_history_row(item) for item in report.history],
        "",
        (
            "- Cumulative direction accuracy: "
            f"{report.cumulative_direction_accuracy:.1f}%"
        ),
        (
            "- Cumulative range accuracy: "
            f"{_optional_percentage(report.cumulative_range_accuracy)}"
        ),
    ]

    _add_coverage_gaps(lines, report)
    _add_history_notes(lines, report)
    lines.extend(
        [
            "",
            "## Suggested weights for next sprint",
            "",
            (
                "These are small trial adjustments from the measured delta, "
                "not proof that one agent caused the final result. The team "
                "should review them before using them."
            ),
            "",
            "| Agent | Current weight | Suggested weight | Reason |",
            "| --- | ---: | ---: | --- |",
            *[
                _render_weight_row(item)
                for item in report.weight_adjustments
            ],
            "",
            "## Prescription for next sprint",
            "",
            report.prescription,
        ]
    )
    return "\n".join(lines) + "\n"


def _add_coverage_gaps(lines: list[str], report: DeltaReport) -> None:
    if not report.missing_prediction_assets and not report.missing_actual_assets:
        return
    lines.extend(["", "## Coverage gaps", ""])
    if report.missing_prediction_assets:
        lines.append(
            "- Missing prediction rows: "
            + join_assets(report.missing_prediction_assets)
        )
    if report.missing_actual_assets:
        lines.append(
            "- Missing actual rows: "
            + join_assets(report.missing_actual_assets)
        )


def _add_history_notes(lines: list[str], report: DeltaReport) -> None:
    if not report.history_notes:
        return
    lines.extend(["", "## History notes", ""])
    lines.extend(f"- {note}" for note in report.history_notes)


def _render_score_row(row: DeltaRow) -> str:
    range_hit = "N/A" if row.range_hit is None else _yes_no(row.range_hit)
    range_error = (
        "N/A" if row.error_percent is None else f"{row.error_percent:.2f}%"
    )
    fields = [
        f"{ASSET_LABELS[row.asset]} ({row.asset})",
        row.predicted_direction,
        row.predicted_range,
        row.confidence,
        f"{row.actual_move:+.2f}%",
        row.actual_direction,
        _yes_no(row.direction_correct),
        range_hit,
        range_error,
    ]
    return "| " + " | ".join(fields) + " |"


def _render_history_row(item: WeekAccuracy) -> str:
    fields = [
        f"v{item.prediction_week}",
        item.actuals_week,
        str(item.scored_assets),
        f"{item.direction_accuracy:.1f}%",
        _optional_percentage(item.range_accuracy),
        f"{item.average_range_error:.2f}%",
    ]
    return "| " + " | ".join(fields) + " |"


def _render_weight_row(item: WeightAdjustment) -> str:
    fields = [
        item.agent,
        f"{item.current_weight:.2f}",
        f"{item.suggested_weight:.2f}",
        item.reason,
    ]
    return "| " + " | ".join(fields) + " |"


def _optional_percentage(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.1f}%"


def _yes_no(value: bool) -> str:
    return "Y" if value else "N"
