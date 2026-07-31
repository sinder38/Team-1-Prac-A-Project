from datetime import datetime, timezone

from tests.server.conftest import app_session
from server.calibration import build_calibration_payload
from server.db import repository as repo


def _delta_data() -> dict:
    return {
        "schema_version": 2,
        "prediction_week": "vW28",
        "rows": [
            {"asset": "SPX"},
            {"asset": "NDX"},
            {"asset": "IWM"},
            {"asset": "XLK"},
        ],
        "history": [
            {
                "prediction_week": "W24",
                "scored_assets": 3,
                "direction_hits": 2,
                "ranged_assets": 3,
                "range_hits": 1,
            },
            {
                "prediction_week": "W28",
                "scored_assets": 4,
                "direction_hits": 3,
                "ranged_assets": 3,
                "range_hits": 2,
            },
        ],
        "weight_adjustments": [
            {"agent": "technical", "suggested_weight": 0.30},
            {"agent": "human_score", "suggested_weight": 0.20},
        ],
        "prescription": "Review the missed ranges.",
    }


def _seed_delta(app, data: dict) -> None:
    with app_session(app) as session:
        repo.add_delta_report(
            session,
            None,
            prediction_week=data.get("prediction_week"),
            schema_version=data.get("schema_version"),
            payload=data,
        )


def test_build_calibration_payload_maps_real_delta_data():
    modified = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)

    payload = build_calibration_payload(_delta_data(), modified)

    assert payload["currentAccuracy"] == 71.4
    assert payload["rangeAccuracy"] == 50.0
    # (2+3)+(1+2) hits / (3+4)+(3+3) attempts = 8/13
    assert payload["totalAccuracy"] == 61.5
    assert payload["latestDirectionAccuracy"] == 75.0
    assert payload["sectorCoverage"] == 1
    assert payload["suggestedWeights"]["technical"] == 30.0
    assert payload["lastCalculated"] == modified.isoformat()


def test_accuracy_tracker_returns_latest_delta(client, app):
    _seed_delta(app, _delta_data())

    response = client.get("/calibration/accuracy-tracker")

    assert response.status_code == 200
    assert response.get_json()["latestWeek"] == "vW28"


def test_accuracy_tracker_skips_old_schema(client, app):
    # A newer week with an old schema version must not win over the valid one.
    old = {"prediction_week": "vW29", "schema_version": 1}
    _seed_delta(app, old)
    _seed_delta(app, _delta_data())

    response = client.get("/calibration/accuracy-tracker")

    assert response.status_code == 200
    assert response.get_json()["latestWeek"] == "vW28"


def test_accuracy_tracker_returns_404_without_delta(client):
    response = client.get("/calibration/accuracy-tracker")

    assert response.status_code == 404
    assert "error" in response.get_json()
