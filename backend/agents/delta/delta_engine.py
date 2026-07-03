"""Delta Engine for Week 5.

The engine compares a locked prediction against the matching actuals file.
It works like a fifth agent: parse the old prediction, compare it with actuals,
then suggest small weight changes for the next sprint.
"""

from dataclasses import asdict
from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Mapping

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
class WeightAdjustment:
    agent: str
    current_weight: float
    suggested_weight: float
    reason: str


@dataclass(frozen=True)
class DeltaReport:
    prediction_week: str
    actuals_week: str
    rows: list[DeltaRow]
    weight_adjustments: list[WeightAdjustment]
    prescription: str

    @property
    def direction_correct_count(self) -> int:
        return sum(1 for row in self.rows if row.direction_correct)

    @property
    def range_hit_count(self) -> int:
        return sum(1 for row in self.rows if row.range_hit)

    @property
    def average_error_percent(self) -> float:
        if not self.rows:
            return 0.0
        return round(
            sum(row.error_percent for row in self.rows) / len(self.rows),
            2,
        )


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
        weight_adjustments = suggest_weight_adjustments(rows)
        return DeltaReport(
            prediction_week=prediction_week,
            actuals_week=actuals_week,
            rows=rows,
            weight_adjustments=weight_adjustments,
            prescription=build_prescription(rows, weight_adjustments),
        )

    def render_markdown(self, report: DeltaReport) -> str:
        return render_delta_markdown(report)

    def write_markdown(self, report: DeltaReport, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.render_markdown(report), encoding="utf-8")
        return output_path

    def render_json(self, report: DeltaReport) -> str:
        return json.dumps(asdict(report), indent=2)

    def write_json(self, report: DeltaReport, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.render_json(report), encoding="utf-8")
        return output_path


class DeltaAgent:
    """Fifth-agent wrapper around DeltaEngine.

    The other agents explain the next prediction. This one reviews the previous
    prediction and turns the miss into a small prescription for the next sprint.
    """

    agent_type = "delta"

    def __init__(self, repo_root: Path | None = None):
        self.repo_root = repo_root or Path(__file__).resolve().parents[3]
        self.engine = DeltaEngine(repo_root=self.repo_root)

    def run(
        self,
        prediction_week: str,
        actuals_week: str,
        prediction_path: Path | None = None,
        actuals_path: Path | None = None,
    ) -> DeltaReport:
        prediction_path = prediction_path or self._prediction_path(prediction_week)
        actuals_path = actuals_path or self._actuals_path(actuals_week)
        return self.engine.run(
            prediction_path=prediction_path,
            actuals_path=actuals_path,
            prediction_week=f"v{prediction_week}",
            actuals_week=actuals_week,
        )

    def write_outputs(
        self,
        report: DeltaReport,
        markdown_path: Path | None = None,
        json_path: Path | None = None,
    ) -> tuple[Path, Path]:
        week = _plain_week(report.prediction_week)
        markdown_path = markdown_path or self.repo_root / "data" / "qa" / f"delta_{week}.md"
        json_path = json_path or self.repo_root / "data" / "outputs" / "delta" / f"delta_{week}.json"
        return (
            self.engine.write_markdown(report, markdown_path),
            self.engine.write_json(report, json_path),
        )

    def _prediction_path(self, week: str) -> Path:
        return (
            self.repo_root
            / "data"
            / "final prediction"
            / f"prediction_2026-{week}_Team1.md"
        )

    def _actuals_path(self, week: str) -> Path:
        return self.repo_root / "data" / "evidence" / f"actuals_{week}.md"


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


def suggest_weight_adjustments(rows: list[DeltaRow]) -> list[WeightAdjustment]:
    direction_hits = sum(1 for row in rows if row.direction_correct)
    range_hits = sum(1 for row in rows if row.range_hit)
    total = len(rows)

    # Starting weights are simple and visible so the team can debate them.
    base_weights = {
        "almanac": 0.20,
        "macro": 0.25,
        "technical": 0.25,
        "llm": 0.20,
        "human_score": 0.10,
    }
    suggested = dict(base_weights)
    reasons = {
        "almanac": "Seasonality stays useful, but delta did not show it should dominate.",
        "macro": "Macro stays important because weekly moves can still depend on rates, oil, and event risk.",
        "technical": "Technical gets a range-check boost because direction was right but one range was too tight.",
        "llm": "LLM weight stays stable until we have more weekly history.",
        "human_score": "Human Score gets a small boost because the final direction call worked.",
    }

    if direction_hits == total and range_hits < total:
        suggested["technical"] += 0.05
        suggested["human_score"] += 0.05
        suggested["almanac"] -= 0.05
        suggested["llm"] -= 0.05
    elif direction_hits < total:
        suggested["human_score"] += 0.05
        suggested["macro"] += 0.05
        suggested["llm"] -= 0.05
        suggested["almanac"] -= 0.05

    return [
        WeightAdjustment(
            agent=agent,
            current_weight=base_weights[agent],
            suggested_weight=round(suggested[agent], 2),
            reason=reasons[agent],
        )
        for agent in ("almanac", "macro", "technical", "llm", "human_score")
    ]


def build_prescription(
    rows: list[DeltaRow],
    adjustments: list[WeightAdjustment],
) -> str:
    missed_ranges = [row.asset for row in rows if not row.range_hit]
    wrong_directions = [row.asset for row in rows if not row.direction_correct]

    if wrong_directions:
        return (
            f"Next sprint should review direction logic for {_join_assets(wrong_directions)} "
            "before locking the final call."
        )
    if missed_ranges:
        changed = [
            item for item in adjustments
            if item.current_weight != item.suggested_weight
        ]
        changed_text = ", ".join(
            f"{item.agent} {item.current_weight:.2f}->{item.suggested_weight:.2f}"
            for item in changed
        )
        return (
            f"Direction was right, but {_join_assets(missed_ranges)} moved outside the range. "
            f"Next sprint should widen range checks and use these draft weights: {changed_text}."
        )
    return (
        "Direction and ranges were both strong. Keep the current weights, but keep "
        "tracking the next result before making a bigger change."
    )


def render_delta_markdown(report: DeltaReport) -> str:
    rows = "\n".join(_render_table_row(row) for row in report.rows)
    weights = "\n".join(_render_weight_row(row) for row in report.weight_adjustments)
    total = len(report.rows)
    short_note = _build_short_note(report)
    week = _plain_week(report.prediction_week)

    return f"""# delta_{week}.md

Role: Delta Engine / Calibration Engine
Status: Generated from locked prediction and matching actuals

## What this checks

This file compares the locked {report.prediction_week} prediction with the matching {report.actuals_week} actuals. The goal is simple: check whether the team got the direction right and how far the actual move was from the predicted range.

## Delta table

| Asset | Predicted direction | Predicted range | Confidence | Actual move | Actual direction | Direction correct? | Range hit? | Error % |
| --- | --- | ---: | --- | ---: | --- | --- | --- | ---: |
{rows}

## Summary

- Direction accuracy: {report.direction_correct_count} / {total}
- Range accuracy: {report.range_hit_count} / {total}
- Average range error: {report.average_error_percent:.2f}%

## Short note

{short_note}

## Weight adjustment draft

This is the Delta Engine's first draft of how the next sprint weights could change. It is not a final team decision; it is a structured starting point for the next prediction cycle.

| Agent | Current weight | Suggested weight | Reason |
| --- | ---: | ---: | --- |
{weights}

## Prescription for next sprint

{report.prescription}
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


def _render_weight_row(row: WeightAdjustment) -> str:
    return (
        f"| {row.agent} | {row.current_weight:.2f} | "
        f"{row.suggested_weight:.2f} | {row.reason} |"
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


def _plain_week(week: str) -> str:
    return week[1:] if week.startswith("vW") else week


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


def _require_assets(rows: Mapping[str, object], label: str) -> None:
    missing = [asset for asset in TRACKED_ASSETS if asset not in rows]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Missing {label} rows for: {joined}")
