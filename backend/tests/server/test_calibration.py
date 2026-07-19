import json
from unittest.mock import patch

import pytest

from server import create_app
from server.calibration import build_calibration_payload, load_latest_delta


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


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


def test_load_latest_delta_skips_old_schema(tmp_path):
    output_dir = tmp_path / "delta"
    output_dir.mkdir()
    (output_dir / "delta_W29.json").write_text(
        json.dumps({"prediction_week": "vW29"}),
        encoding="utf-8",
    )
    valid_path = output_dir / "delta_W28.json"
    valid_path.write_text(json.dumps(_delta_data()), encoding="utf-8")

    path, data = load_latest_delta(output_dir)

    assert path == valid_path
    assert data["prediction_week"] == "vW28"


def test_build_calibration_payload_maps_real_delta_data(tmp_path):
    path = tmp_path / "delta_W28.json"
    path.write_text("{}", encoding="utf-8")

    payload = build_calibration_payload(_delta_data(), path)

    assert payload["currentAccuracy"] == 71.4
    assert payload["rangeAccuracy"] == 50.0
    assert payload["latestDirectionAccuracy"] == 75.0
    assert payload["sectorCoverage"] == 1
    assert payload["suggestedWeights"]["technical"] == 30.0


def test_accuracy_tracker_returns_latest_delta(client, tmp_path):
    path = tmp_path / "delta_W28.json"
    data = _delta_data()
    path.write_text(json.dumps(data), encoding="utf-8")

    with patch(
        "server.calibration.load_latest_delta",
        return_value=(path, data),
    ):
        response = client.get("/calibration/accuracy-tracker")

    assert response.status_code == 200
    assert response.get_json()["latestWeek"] == "vW28"


def test_accuracy_tracker_returns_404_without_delta(client):
    with patch(
        "server.calibration.load_latest_delta",
        side_effect=FileNotFoundError("No Delta output"),
    ):
        response = client.get("/calibration/accuracy-tracker")

    assert response.status_code == 404
    assert response.get_json()["error"] == "No Delta output"
