"""Read the latest Delta Engine result for the calibration dashboard."""

from datetime import datetime
from typing import Any

from flask import Blueprint, jsonify

from server.db import repository as repo
from server.db.context import db_session
from server.utils import err

calibration_bp = Blueprint(
    "calibration",
    __name__,
    url_prefix="/calibration",
)


@calibration_bp.route("/accuracy-tracker", methods=["GET"])
def get_accuracy_tracker():
    with db_session() as session:
        row = repo.get_latest_delta(session)
        if row is None:
            return err("No valid Delta Engine output is available yet.", 404)
        data = row.payload
        modified = row.created_at
    try:
        payload = build_calibration_payload(data, modified)
    except (KeyError, TypeError, ValueError) as exc:
        return err(f"Invalid Delta Engine output: {exc}", 500)
    return jsonify(payload), 200


def build_calibration_payload(
    data: dict[str, Any],
    modified: datetime,
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

    direction_accuracy = _percentage(all_direction_hits, all_scored_assets)
    range_accuracy = _percentage(all_range_hits, all_ranged_assets)
    # Combined hit-rate across both scoring dimensions (sample-weighted).
    total_accuracy = _percentage(
        all_direction_hits + all_range_hits,
        all_scored_assets + all_ranged_assets,
    )

    return {
        "latestWeek": data.get("prediction_week"),
        "totalAccuracy": total_accuracy,
        "currentAccuracy": direction_accuracy,
        "rangeAccuracy": range_accuracy,
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
