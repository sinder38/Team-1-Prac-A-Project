"""Delta Engine agent for weekly review and retrospective feedback.

The engine scores only a completed week. The agent then adds earlier valid
week pairs, proposes a small weight change, and writes Markdown plus JSON for
the next pipeline cycle.
"""

import json
import re
from dataclasses import asdict, replace
from pathlib import Path
from typing import Mapping

from agents.delta.models import (
    AGENT_ORDER,
    BASE_WEIGHTS,
    ActualRow,
    DeltaReport,
    PredictionRow,
    WeekAccuracy,
)
from agents.delta.parsing import (
    next_week,
    parse_actuals_file,
    parse_actuals_markdown,
    parse_prediction_file,
    parse_prediction_markdown,
    plain_week,
    validate_week_pair,
    versioned_week,
    week_number,
)
from agents.delta.report import render_delta_markdown
from agents.delta.scoring import (
    build_prescription,
    score_available_assets,
    suggest_weight_adjustments,
    summarize_week,
)


class DeltaEngine:
    """Compare one locked prediction with its matching actuals."""

    def run(
        self,
        prediction_path: Path,
        actuals_path: Path,
        prediction_week: str,
        actuals_week: str,
        current_weights: Mapping[str, float] | None = None,
    ) -> DeltaReport:
        prediction_week = plain_week(prediction_week)
        actuals_week = plain_week(actuals_week)
        validate_week_pair(prediction_week, actuals_week)

        predictions = parse_prediction_file(prediction_path)
        actuals = parse_actuals_file(actuals_path)
        return self._build_report(
            predictions,
            actuals,
            prediction_week,
            actuals_week,
            current_weights,
        )

    def run_with_actuals_markdown(
        self,
        prediction_path: Path,
        actuals_markdown: str,
        prediction_week: str,
        actuals_week: str,
        current_weights: Mapping[str, float] | None = None,
    ) -> DeltaReport:
        """Score a saved prediction against Evidence API markdown."""
        prediction_week = plain_week(prediction_week)
        actuals_week = plain_week(actuals_week)
        validate_week_pair(prediction_week, actuals_week)

        predictions = parse_prediction_file(prediction_path)
        actuals = parse_actuals_markdown(actuals_markdown)
        return self._build_report(
            predictions,
            actuals,
            prediction_week,
            actuals_week,
            current_weights,
        )

    @staticmethod
    def _build_report(
        predictions: Mapping[str, PredictionRow],
        actuals: Mapping[str, ActualRow],
        prediction_week: str,
        actuals_week: str,
        current_weights: Mapping[str, float] | None,
    ) -> DeltaReport:
        rows, missing_predictions, missing_actuals = score_available_assets(
            predictions,
            actuals,
        )
        history = [summarize_week(prediction_week, actuals_week, rows)]
        weights = current_weights or BASE_WEIGHTS
        adjustments = suggest_weight_adjustments(rows, history, weights)

        return DeltaReport(
            schema_version=2,
            prediction_week=versioned_week(prediction_week),
            actuals_week=actuals_week,
            rows=rows,
            missing_prediction_assets=missing_predictions,
            missing_actual_assets=missing_actuals,
            history=history,
            history_notes=[],
            weight_adjustments=adjustments,
            prescription=build_prescription(
                rows,
                missing_predictions,
                adjustments,
            ),
        )

    @staticmethod
    def render_markdown(report: DeltaReport) -> str:
        return render_delta_markdown(report)

    def write_markdown(self, report: DeltaReport, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.render_markdown(report), encoding="utf-8")
        return output_path

    @staticmethod
    def render_json(report: DeltaReport) -> str:
        return json.dumps(asdict(report), indent=2)

    def write_json(self, report: DeltaReport, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.render_json(report), encoding="utf-8")
        return output_path


class DeltaAgent:
    """Add repository paths and cumulative history around DeltaEngine."""

    agent_type = "delta"

    def __init__(self, repo_root: Path | None = None):
        self.repo_root = repo_root or Path(__file__).resolve().parents[3]
        self.engine = DeltaEngine()

    def run(
        self,
        prediction_week: str,
        actuals_week: str,
        prediction_path: Path | None = None,
        actuals_path: Path | None = None,
        actuals_markdown: str | None = None,
        include_history: bool = True,
    ) -> DeltaReport:
        prediction_week = plain_week(prediction_week)
        actuals_week = plain_week(actuals_week)
        validate_week_pair(prediction_week, actuals_week)

        current_weights = self._latest_weights_before(prediction_week)
        locked_prediction = prediction_path or self._prediction_path(
            prediction_week
        )
        if actuals_markdown is None:
            report = self.engine.run(
                prediction_path=locked_prediction,
                actuals_path=actuals_path or self._actuals_path(actuals_week),
                prediction_week=prediction_week,
                actuals_week=actuals_week,
                current_weights=current_weights,
            )
        else:
            report = self.engine.run_with_actuals_markdown(
                prediction_path=locked_prediction,
                actuals_markdown=actuals_markdown,
                prediction_week=prediction_week,
                actuals_week=actuals_week,
                current_weights=current_weights,
            )
        if not include_history:
            return report

        history, notes = self._build_history(prediction_week, report)
        adjustments = suggest_weight_adjustments(
            report.rows,
            history,
            current_weights,
        )
        return replace(
            report,
            history=history,
            history_notes=notes,
            weight_adjustments=adjustments,
            prescription=build_prescription(
                report.rows,
                report.missing_prediction_assets,
                adjustments,
            ),
        )

    def write_outputs(
        self,
        report: DeltaReport,
        markdown_path: Path | None = None,
        json_path: Path | None = None,
    ) -> tuple[Path, Path]:
        week = plain_week(report.prediction_week)
        markdown_path = markdown_path or (
            self.repo_root / "data" / "qa" / f"delta_{week}.md"
        )
        json_path = json_path or (
            self.repo_root
            / "data"
            / "outputs"
            / "delta"
            / f"delta_{week}.json"
        )
        return (
            self.engine.write_markdown(report, markdown_path),
            self.engine.write_json(report, json_path),
        )

    def _prediction_path(self, week: str) -> Path:
        prediction_dir = self.repo_root / "data" / "final prediction"
        candidates = (
            prediction_dir / f"prediction_2026-{week}_Team1.md",
            prediction_dir / f"prediction_2026_{week}_Team1.md",
            prediction_dir / f"prediction_{week}.md",
            prediction_dir / f"prediction_{week}.json",
        )
        for path in candidates:
            if path.exists():
                return path
        names = ", ".join(path.name for path in candidates)
        raise FileNotFoundError(
            f"No locked prediction found for {week}. Checked: {names}"
        )

    def _actuals_path(self, week: str) -> Path:
        path = self.repo_root / "data" / "evidence" / f"actuals_{week}.md"
        if not path.exists():
            raise FileNotFoundError(f"Actuals file not found: {path}")
        return path

    def _build_history(
        self,
        target_week: str,
        current_report: DeltaReport,
    ) -> tuple[list[WeekAccuracy], list[str]]:
        history: list[WeekAccuracy] = []
        notes: list[str] = []

        for week, path in self._available_prediction_files().items():
            if week_number(week) > week_number(target_week):
                continue
            if week == target_week:
                history.append(current_report.history[0])
                continue

            actuals_week = next_week(week)
            actuals_path = (
                self.repo_root
                / "data"
                / "evidence"
                / f"actuals_{actuals_week}.md"
            )
            if not actuals_path.exists():
                notes.append(
                    f"{week} was not scored because actuals_{actuals_week}.md "
                    "is missing."
                )
                continue

            try:
                predictions = parse_prediction_file(path)
                actuals = parse_actuals_file(actuals_path)
                rows, _, _ = score_available_assets(predictions, actuals)
            except (FileNotFoundError, ValueError) as exc:
                notes.append(f"{week} was not scored: {exc}")
                continue
            history.append(summarize_week(week, actuals_week, rows))

        if not any(
            item.prediction_week == target_week for item in history
        ):
            history.append(current_report.history[0])
        history.sort(key=lambda item: week_number(item.prediction_week))
        return history, notes

    def _available_prediction_files(self) -> dict[str, Path]:
        prediction_dir = self.repo_root / "data" / "final prediction"
        if not prediction_dir.exists():
            return {}

        paths: dict[str, Path] = {}
        for suffix in ("md", "json"):
            for path in sorted(prediction_dir.glob(f"prediction_*.{suffix}")):
                match = re.search(r"(?:-|_)(W\d{2})(?:_|\.)", path.name)
                if match:
                    paths[match.group(1)] = path
        return paths

    def _latest_weights_before(self, target_week: str) -> dict[str, float]:
        output_dir = self.repo_root / "data" / "outputs" / "delta"
        candidates: list[tuple[int, Path]] = []
        if output_dir.exists():
            for path in output_dir.glob("delta_W*.json"):
                match = re.fullmatch(r"delta_W(\d{2})\.json", path.name)
                if match and int(match.group(1)) < week_number(target_week):
                    candidates.append((int(match.group(1)), path))

        for _, path in sorted(candidates, reverse=True):
            weights = _read_suggested_weights(path)
            if weights is not None:
                return weights
        return dict(BASE_WEIGHTS)


def _read_suggested_weights(path: Path) -> dict[str, float] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema_version") != 2:
            return None
        weights = {
            item["agent"]: float(item["suggested_weight"])
            for item in data.get("weight_adjustments", [])
        }
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None
    return weights if set(weights) == set(AGENT_ORDER) else None


__all__ = [
    "DeltaAgent",
    "DeltaEngine",
    "parse_actuals_markdown",
    "parse_prediction_markdown",
]
