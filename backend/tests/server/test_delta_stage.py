import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from agents.delta.models import DeltaReport, WeekAccuracy
from server import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def _report() -> DeltaReport:
    return DeltaReport(
        schema_version=2,
        prediction_week="vW28",
        actuals_week="W29",
        rows=[],
        missing_prediction_assets=[],
        missing_actual_assets=[],
        history=[
            WeekAccuracy(
                prediction_week="W28",
                actuals_week="W29",
                scored_assets=3,
                direction_hits=2,
                ranged_assets=3,
                range_hits=1,
                average_range_error=0.5,
            )
        ],
        history_notes=[],
        weight_adjustments=[],
        prescription="Review the missed range before the next lock.",
    )


def test_post_delta_runs_pipeline_stage(client, tmp_path):
    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_text(
        json.dumps(
            {
                "content": "# Completed actuals",
                "generated_at": "2026-07-17T21:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    def set_delta(ctx, config, actuals_markdown, now):
        assert actuals_markdown == "# Completed actuals"
        assert config.artifacts.save_md is True
        assert now.isoformat() == "2026-07-17T21:00:00+00:00"
        ctx.delta = _report()

    with (
        patch("server.stages.artifact_path", return_value=evidence_path),
        patch("server.stages.run_delta", side_effect=set_delta) as run_delta,
    ):
        response = client.post(
            "/stages/delta",
            json={"prediction_date": "2026-07-13", "run_id": "run1"},
        )

    assert response.status_code == 200
    assert response.get_json()["prediction_week"] == "vW28"
    assert run_delta.call_args.args[0].prediction_date == date(2026, 7, 13)


def test_post_delta_requires_prediction_date(client):
    response = client.post("/stages/delta", json={"run_id": "run1"})

    assert response.status_code == 400
    assert "prediction_date" in response.get_json()["error"]


def test_post_delta_reports_missing_week_files(client):
    with patch(
        "server.stages.artifact_path",
        return_value=Path("missing-evidence.json"),
    ):
        response = client.post(
            "/stages/delta",
            json={"prediction_date": "2026-07-13", "run_id": "run1"},
        )

    assert response.status_code == 404
    assert "Evidence artifact not found" in response.get_json()["error"]
