"""Delta Engine for Week 5.

The engine compares a locked prediction against the matching actuals file.
It keeps the logic small on purpose: parse the three index rows, score them,
then render a markdown report that R10 can review before submission.
"""

from dataclasses import dataclass
from pathlib import Path
import re

TRACKED_ASSETS = ("SPX", "NDX", "IWM")


@dataclass(frozen=True)
class PredictionRow:
    asset: str
    direction: str
    range_low: float
    range_high: float
    confidence: str


@dataclass(frozen=True)
class ActualRow:
    asset: str
    actual_move: float
    actual_direction: str


@dataclass(frozen=True)
class DeltaRow:
    asset: str
    predicted_direction: str
    predicted_range: str
    confidence: str
    actual_move: float
    actual_direction: str
    direction_correct: bool
    range_hit: bool
    error_percent: float


@dataclass(frozen=True)
class DeltaReport:
    prediction_week: str
    actuals_week: str
    rows: list[DeltaRow]

    @property
    def direction_correct_count(self) -> int:
        return sum(1 for row in self.rows if row.direction_correct)

    @property
    def range_hit_count(self) -> int:
        return sum(1 for row in self.rows if row.range_hit)


class DeltaEngine:
    """Compare prediction and actuals markdown files for SPX, NDX, and IWM."""

    def __init__(self, repo_root: Path | None = None):
        self.repo_root = repo_root or Path(__file__).resolve().parents[3]

    def run(
        self,
        prediction_path: Path,
        actuals_path: Path,
        prediction_week: str,
        actuals_week: str,
    ) -> DeltaReport:
        predictions = parse_prediction_file(prediction_path)
        actuals = parse_actuals_file(actuals_path)

        rows = [
            score_asset(predictions[asset], actuals[asset])
            for asset in TRACKED_ASSETS
        ]
        return DeltaReport(
            prediction_week=prediction_week,
            actuals_week=actuals_week,
            rows=rows,
        )

    def render_markdown(self, report: DeltaReport) -> str:
        return render_delta_markdown(report)

    def write_markdown(self, report: DeltaReport, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.render_markdown(report), encoding="utf-8")
        return output_path


def parse_prediction_file(path: Path) -> dict[str, PredictionRow]:
    if not path.exists():
        raise FileNotFoundError(f"Prediction file not found: {path}")
    return parse_prediction_markdown(path.read_text(encoding="utf-8"))


def parse_actuals_file(path: Path) -> dict[str, ActualRow]:
    if not path.exists():
        raise FileNotFoundError(f"Actuals file not found: {path}")
    return parse_actuals_markdown(path.read_text(encoding="utf-8"))


def parse_prediction_markdown(markdown: str) -> dict[str, PredictionRow]:
    rows: dict[str, PredictionRow] = {}
    for line in markdown.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = _table_cells(line)
        if len(cells) < 4:
            continue

        asset = _asset_from_text(cells[0])
        if asset not in TRACKED_ASSETS:
            continue

        direction = _clean_markdown(cells[1]).upper()
        range_low, range_high = _parse_percent_range(cells[2])
        confidence = _clean_markdown(cells[3]).title()

        rows[asset] = PredictionRow(
            asset=asset,
            direction=direction,
            range_low=range_low,
            range_high=range_high,
            confidence=confidence,
        )

    _require_assets(rows, "prediction")
    return rows


def parse_actuals_markdown(markdown: str) -> dict[str, ActualRow]:
    rows: dict[str, ActualRow] = {}
    for line in markdown.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = _table_cells(line)
        if len(cells) < 4:
            continue

        asset = _clean_markdown(cells[1]).upper()
        if asset not in TRACKED_ASSETS:
            continue

        actual_text = _clean_markdown(cells[3])
        move = _parse_single_percent(actual_text)
        direction = _direction_from_actual_text(actual_text, move)
        rows[asset] = ActualRow(
            asset=asset,
            actual_move=move,
            actual_direction=direction,
        )

    _require_assets(rows, "actuals")
    return rows


def score_asset(prediction: PredictionRow, actual: ActualRow) -> DeltaRow:
    direction_correct = _direction_matches(
        prediction.direction,
        actual.actual_direction,
    )
    range_hit = prediction.range_low <= actual.actual_move <= prediction.range_high

    # If the actual move is outside the range, error is distance to the nearest edge.
    if range_hit:
        error_percent = 0.0
    elif actual.actual_move < prediction.range_low:
        error_percent = prediction.range_low - actual.actual_move
    else:
        error_percent = actual.actual_move - prediction.range_high

    return DeltaRow(
        asset=prediction.asset,
        predicted_direction=prediction.direction,
        predicted_range=_format_range(prediction.range_low, prediction.range_high),
        confidence=prediction.confidence,
        actual_move=actual.actual_move,
        actual_direction=actual.actual_direction,
        direction_correct=direction_correct,
        range_hit=range_hit,
        error_percent=round(error_percent, 2),
    )


def render_delta_markdown(report: DeltaReport) -> str:
    rows = "\n".join(_render_table_row(row) for row in report.rows)
    total = len(report.rows)
    short_note = _build_short_note(report)

    return f"""# delta_W24.md

Role: Delta Engine / R10 support
Status: Draft for team review

## What this checks

This file compares the locked {report.prediction_week} prediction with the matching {report.actuals_week} actuals. The goal is simple: check whether the team got the direction right and how far the actual move was from the predicted range.

## Delta table

| Asset | Predicted direction | Predicted range | Confidence | Actual move | Actual direction | Direction correct? | Range hit? | Error % |
| --- | --- | ---: | --- | ---: | --- | --- | --- | ---: |
{rows}

## Summary

- Direction accuracy: {report.direction_correct_count} / {total}
- Range accuracy: {report.range_hit_count} / {total}

## Short note

{short_note}
"""


def _render_table_row(row: DeltaRow) -> str:
    direction = "Y" if row.direction_correct else "N"
    range_hit = "Y" if row.range_hit else "N"
    actual_move = f"{row.actual_move:+.2f}%"
    return (
        f"| {row.asset} | {row.predicted_direction} | {row.predicted_range} | "
        f"{row.confidence} | {actual_move} | {row.actual_direction} | "
        f"{direction} | {range_hit} | {row.error_percent:.2f}% |"
    )


def _build_short_note(report: DeltaReport) -> str:
    total = len(report.rows)
    inside = [row.asset for row in report.rows if row.range_hit]
    missed = [row.asset for row in report.rows if not row.range_hit]

    if report.direction_correct_count == total:
        direction_note = "The team got the broad direction right across all three indexes."
    elif report.direction_correct_count == 0:
        direction_note = "The team missed the direction across all three indexes."
    else:
        direction_note = (
            f"The team got {report.direction_correct_count} of {total} directions right."
        )

    if missed:
        range_note = (
            f"{_join_assets(inside)} landed inside the predicted range, "
            f"while {', '.join(missed)} finished outside the range."
        )
    else:
        range_note = "All three actual moves landed inside the predicted ranges."

    return (
        f"{direction_note} {range_note} My main takeaway is that the direction "
        "call was useful, but the range still needs checking when one index "
        "moves more strongly than the others."
    )


def _join_assets(assets: list[str]) -> str:
    if not assets:
        return "No index"
    if len(assets) == 1:
        return assets[0]
    return f"{', '.join(assets[:-1])} and {assets[-1]}"


def _table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _clean_markdown(text: str) -> str:
    text = re.sub(r"[*_`]", "", text)
    return text.strip()


def _asset_from_text(text: str) -> str:
    match = re.search(r"\b(SPX|NDX|IWM)\b", text.upper())
    return match.group(1) if match else ""


def _parse_percent_range(text: str) -> tuple[float, float]:
    values = [float(value) for value in re.findall(r"[-+]?\d+(?:\.\d+)?", text)]
    if len(values) < 2:
        raise ValueError(f"Could not read prediction range: {text!r}")
    low, high = values[0], values[1]
    return (min(low, high), max(low, high))


def _parse_single_percent(text: str) -> float:
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    if not match:
        raise ValueError(f"Could not read actual percentage: {text!r}")
    value = float(match.group(0))
    if "down" in text.lower() and value > 0:
        return -value
    return value


def _direction_from_actual_text(text: str, move: float) -> str:
    lowered = text.lower()
    if "down" in lowered:
        return "DOWN"
    if "up" in lowered:
        return "UP"
    if abs(move) < 0.05:
        return "FLAT"
    return "UP" if move > 0 else "DOWN"


def _direction_matches(predicted: str, actual: str) -> bool:
    predicted_parts = {part.strip() for part in predicted.upper().split("-")}
    if actual == "FLAT":
        return "FLAT" in predicted_parts
    return actual in predicted_parts


def _format_range(low: float, high: float) -> str:
    return f"{low:+.1f}% to {high:+.1f}%"


def _require_assets(rows: dict[str, object], label: str) -> None:
    missing = [asset for asset in TRACKED_ASSETS if asset not in rows]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Missing {label} rows for: {joined}")
