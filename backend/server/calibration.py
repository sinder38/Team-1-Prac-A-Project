"""Read the latest Delta Engine result for the calibration dashboard."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Blueprint, jsonify

from agents.paths import OUTPUTS_DIR
from server.utils import err

calibration_bp = Blueprint(
    "calibration",
    __name__,
    url_prefix="/calibration",
)
DELTA_OUTPUT_DIR = OUTPUTS_DIR / "delta"


@calibration_bp.route("/accuracy-tracker", methods=["GET"])
def get_accuracy_tracker():
    try:
        path, data = load_latest_delta(DELTA_OUTPUT_DIR)
        payload = build_calibration_payload(data, path)
    except FileNotFoundError as exc:
        return err(str(exc), 404)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return err(f"Invalid Delta Engine output: {exc}", 500)
    return jsonify(payload), 200


def load_latest_delta(output_dir: Path) -> tuple[Path, dict[str, Any]]:
    """Return the latest valid v2 Delta artifact by prediction week."""
    candidates: list[tuple[int, Path]] = []
    if output_dir.exists():
        for path in output_dir.glob("delta_W*.json"):
            match = re.fullmatch(r"delta_W(\d{2})\.json", path.name)
            if match:
                candidates.append((int(match.group(1)), path))

    for _, path in sorted(candidates, reverse=True):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema_version") == 2:
            return path, data
    raise FileNotFoundError("No valid Delta Engine output is available yet.")


def build_calibration_payload(
    data: dict[str, Any],
    path: Path,
) -> dict[str, Any]:
    history = data.get("history")
    rows = data.get("rows")
    adjustments = data.get("weight_adjustments")
    if not isinstance(history, list) or not history:
        raise ValueError("history must contain at least one scored week")
    if not isinstance(rows, list) or not isinstance(adjustments, list):
        raise ValueError("rows and weight_adjustments must be lists")

    weekly_trend = [_history_point(item) for item in history]
    latest = weekly_trend[-1]
    all_direction_hits = sum(int(item["direction_hits"]) for item in history)
    all_scored_assets = sum(int(item["scored_assets"]) for item in history)
    all_range_hits = sum(int(item["range_hits"]) for item in history)
    all_ranged_assets = sum(int(item["ranged_assets"]) for item in history)

    sector_tickers = {
        "XLK",
        "XLV",
        "XLF",
        "XLY",
        "XLC",
        "XLI",
        "XLP",
        "XLE",
        "XLB",
        "XLRE",
        "XLU",
    }
    sector_coverage = sum(1 for row in rows if row.get("asset") in sector_tickers)
    suggested_weights = {
        str(item["agent"]): round(float(item["suggested_weight"]) * 100, 1)
        for item in adjustments
    }
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)

    return {
        "latestWeek": data.get("prediction_week"),
        "currentAccuracy": _percentage(
            all_direction_hits,
            all_scored_assets,
        ),
        "rangeAccuracy": _percentage(all_range_hits, all_ranged_assets),
        "weeklyTrend": weekly_trend,
        "latestDirectionAccuracy": latest["directionAccuracy"],
        "latestRangeAccuracy": latest["rangeAccuracy"],
        "sectorCoverage": sector_coverage,
        "sectorTotal": len(sector_tickers),
        "suggestedWeights": suggested_weights,
        "prescription": data.get("prescription", ""),
        "lastCalculated": modified.isoformat(),
    }


def _history_point(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "week": item["prediction_week"],
        "directionAccuracy": _percentage(
            int(item["direction_hits"]),
            int(item["scored_assets"]),
        ),
        "rangeAccuracy": _percentage(
            int(item["range_hits"]),
            int(item["ranged_assets"]),
        ),
    }


def _percentage(numerator: int, denominator: int) -> float:
    if not denominator:
        return 0.0
    return round(numerator / denominator * 100.0, 1)
