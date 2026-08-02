"""Compare locked predictions with completed weekly actuals."""

import json
import re
from dataclasses import asdict
from pathlib import Path

from agents.delta.models import (
    AGENT_ORDER,
    BASE_WEIGHTS,
    DeltaReport,
    WeekAccuracy,
)
from agents.delta.parsing import (
    artifact_week,
    next_week,
    parse_actuals_file,
    parse_actuals_markdown,
    parse_prediction_file,
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


class DeltaAgent:
    """Run the Delta review and keep its cumulative history."""

    agent_type = "delta"

    def __init__(self, repo_root: Path | None = None):
        self.repo_root = repo_root or Path(__file__).resolve().parents[3]

    def run(
        self,
        prediction_week: str,
        actuals_week: str,
        prediction_path: Path | None = None,
        actuals_path: Path | None = None,
        actuals_markdown: str | None = None,
    ) -> DeltaReport:
        """Score one completed pair and add earlier valid week pairs."""
        # Week labels may arrive as W24 or vW24. Convert both forms to W24
        # before checking that the prediction and actuals are one week apart.
        prediction_week = plain_week(prediction_week)
        actuals_week = plain_week(actuals_week)
        validate_week_pair(prediction_week, actuals_week)

        # Use custom paths when the caller supplies them. Otherwise, look for
        # the files in the normal project folders.
        prediction_path = prediction_path or self._prediction_path(prediction_week)
        predictions = parse_prediction_file(prediction_path)
        if actuals_markdown is None:
            actuals_path = actuals_path or self._actuals_path(actuals_week)
            actuals = parse_actuals_file(actuals_path)
        else:
            actuals = parse_actuals_markdown(actuals_markdown)

        # Only score assets that appear in both files. Missing rows are kept
        # in the report so the team can fix its evidence next week.
        rows, missing_predictions, missing_actuals = score_available_assets(
            predictions,
            actuals,
        )
        current_week = summarize_week(
            prediction_week,
            actuals_week,
            rows,
        )

        # Earlier valid week pairs provide cumulative accuracy. The current
        # week is included in the same history before weights are reviewed.
        history, history_notes = self._build_history(
            prediction_week,
            current_week,
        )
        current_weights = self._latest_weights_before(prediction_week)
        adjustments = suggest_weight_adjustments(
            rows,
            history,
            current_weights,
        )

        # DeltaReport is the single result used by the CLI, API and frontend.
        return DeltaReport(
            schema_version=2,
            prediction_week=versioned_week(prediction_week),
            actuals_week=actuals_week,
            rows=rows,
            missing_prediction_assets=missing_predictions,
            missing_actual_assets=missing_actuals,
            history=history,
            history_notes=history_notes,
            weight_adjustments=adjustments,
            prescription=build_prescription(
                rows,
                missing_predictions,
                adjustments,
            ),
        )

    def write_outputs(
        self,
        report: DeltaReport,
        markdown_path: Path | None = None,
        json_path: Path | None = None,
    ) -> tuple[Path, Path]:
        """Write the human-readable and structured Delta artifacts."""
        # Artifacts are filed under the completed actuals week so the Delta
        # report carries the same W-label as every other artifact of the run.
        week = artifact_week(report.prediction_week, report.actuals_week)
        markdown_path = markdown_path or (
            self.repo_root / "data" / "qa" / f"delta_{week}.md"
        )
        json_path = json_path or (
            self.repo_root / "data" / "outputs" / "delta" / f"delta_{week}.json"
        )
        return (
            self.write_markdown(report, markdown_path),
            self.write_json(report, json_path),
        )

    @staticmethod
    def write_markdown(report: DeltaReport, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_delta_markdown(report), encoding="utf-8")
        return path

    @staticmethod
    def write_json(report: DeltaReport, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(asdict(report), indent=2)
        path.write_text(content, encoding="utf-8")
        return path

    def _prediction_path(self, week: str) -> Path:
        prediction_dir = self.repo_root / "data" / "final prediction"
        # Older weeks used slightly different file names, so check each known
        # project format in a fixed order.
        candidates = (
            prediction_dir / f"prediction_2026-{week}_Team1.md",
            prediction_dir / f"prediction_2026_{week}_Team1.md",
            prediction_dir / f"prediction_{week}.md",
            prediction_dir / f"prediction_{week}.json",
        )
        for path in candidates:
            if path.exists():
                return path

        checked_names = ", ".join(path.name for path in candidates)
        raise FileNotFoundError(
            f"No locked prediction found for {week}. Checked: {checked_names}"
        )

    def _actuals_path(self, week: str) -> Path:
        path = self._actuals_file(week)
        if not path.exists():
            raise FileNotFoundError(f"Actuals file not found: {path}")
        return path

    def _build_history(
        self,
        target_week: str,
        current_week: WeekAccuracy,
    ) -> tuple[list[WeekAccuracy], list[str]]:
        history: list[WeekAccuracy] = []
        notes: list[str] = []
        target_number = week_number(target_week)

        # A historical week is only scored when both its locked prediction
        # and the following week's actuals exist. We never invent missing data.
        for week, prediction_path in self._prediction_files().items():
            if week_number(week) > target_number:
                continue
            if week == target_week:
                history.append(current_week)
                continue

            actuals_week = next_week(week)
            actuals_path = self._actuals_file(actuals_week)
            if not actuals_path.exists():
                notes.append(
                    f"{week} was not scored because {actuals_path.name} is missing."
                )
                continue

            try:
                predictions = parse_prediction_file(prediction_path)
                actuals = parse_actuals_file(actuals_path)
                rows, _, _ = score_available_assets(predictions, actuals)
            except ValueError as exc:
                # One malformed old file should not stop the current report.
                notes.append(f"{week} was not scored: {exc}")
                continue

            history.append(summarize_week(week, actuals_week, rows))

        if current_week not in history:
            history.append(current_week)
        history.sort(key=lambda item: week_number(item.prediction_week))
        return history, notes

    def _prediction_files(self) -> dict[str, Path]:
        prediction_dir = self.repo_root / "data" / "final prediction"
        if not prediction_dir.exists():
            return {}

        paths: dict[str, Path] = {}
        for path in sorted(prediction_dir.glob("prediction_*")):
            if path.suffix.lower() not in {".md", ".json"}:
                continue
            match = re.search(r"(?:-|_)(W\d{2})(?:_|\.)", path.name)
            if match:
                paths[match.group(1)] = path
        return paths

    def _actuals_file(self, week: str) -> Path:
        return self.repo_root / "data" / "evidence" / f"actuals_{week}.md"

    def _latest_weights_before(self, target_week: str) -> dict[str, float]:
        output_dir = self.repo_root / "data" / "outputs" / "delta"
        if not output_dir.exists():
            return dict(BASE_WEIGHTS)

        target_number = week_number(target_week)
        candidates: list[tuple[int, dict[str, float]]] = []
        for path in sorted(output_dir.glob("delta_W*.json")):
            if not re.fullmatch(r"delta_W(\d{2})\.json", path.name):
                continue
            # The week inside the payload is authoritative. File names have
            # carried the prediction week historically and the actuals week
            # today, so trusting the name would double-count or skip reports
            # in a directory that mixes both conventions.
            pair_week, weights = _read_suggested_weights(path)
            if pair_week is None or weights is None:
                continue
            if pair_week < target_number:
                candidates.append((pair_week, weights))

        # Use the newest strictly-earlier prediction pair. If none is valid,
        # fall back to the documented base weights instead of guessing.
        if not candidates:
            return dict(BASE_WEIGHTS)
        candidates.sort(key=lambda item: item[0])
        return candidates[-1][1]


def _read_suggested_weights(
    path: Path,
) -> tuple[int | None, dict[str, float] | None]:
    """Read the pair week and reviewed weights from a structured artifact.

    Returns ``(prediction_week_number, weights)``. Either element is ``None``
    when the file is unreadable, has the wrong schema, or is incomplete, so a
    single damaged artifact can never poison the weight review.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema_version") != 2:
            return None, None
        pair_week = week_number(str(data["prediction_week"]))

        # Use a normal loop here so it is clear which two JSON fields become
        # the key and value in the weights dictionary.
        weights: dict[str, float] = {}
        for item in data.get("weight_adjustments", []):
            agent = item["agent"]
            suggested_weight = float(item["suggested_weight"])
            weights[agent] = suggested_weight
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None, None

    # A partial set could make the total weight incorrect, so only accept a
    # report containing every expected agent.
    if set(weights) != set(AGENT_ORDER):
        return pair_week, None
    return pair_week, weights

__all__ = ["DeltaAgent"]
