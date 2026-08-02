from datetime import date
from unittest.mock import patch

from agents.delta.models import DeltaReport, WeekAccuracy
from tests.server.conftest import seed_agent_output


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


def test_post_delta_runs_pipeline_stage(client, app):
    # Delta reads the evidence artifact for the run from the DB.
    seed_agent_output(
        app,
        run_id="run1",
        prediction_date=date(2026, 7, 13),
        agent_type="evidence",
        payload={
            "content": "# Completed actuals",
            "generated_at": "2026-07-17T21:00:00+00:00",
        },
        horizon_days=None,
    )

    def set_delta(ctx, config, actuals_markdown, now):
        assert actuals_markdown == "# Completed actuals"
        assert config.delta.prediction_week == "previous"
        assert now.isoformat() == "2026-07-17T21:00:00+00:00"
        ctx.delta = _report()

    with patch("server.stages.run_delta", side_effect=set_delta) as run_delta:
        response = client.post(
            "/stages/delta",
            json={"prediction_date": "2026-07-13", "run_id": "run1"},
        )

    assert response.status_code == 200
    assert response.get_json()["prediction_week"] == "vW28"
    assert run_delta.call_args.args[0].prediction_date == date(2026, 7, 13)

    # The delta report was persisted and drives the calibration endpoint.
    tracker = client.get("/calibration/accuracy-tracker")
    assert tracker.status_code == 200
    assert tracker.get_json()["latestWeek"] == "vW28"


def test_post_delta_requires_prediction_date(client):
    response = client.post("/stages/delta", json={"run_id": "run1"})

    assert response.status_code == 400
    assert "prediction_date" in response.get_json()["error"]


def test_post_delta_reports_missing_evidence(client):
    # No evidence artifact seeded for run1.
    response = client.post(
        "/stages/delta",
        json={"prediction_date": "2026-07-13", "run_id": "run1"},
    )

    assert response.status_code == 404
    assert "Evidence artifact not found" in response.get_json()["error"]


def test_post_delta_reports_output_collision(client, app):
    seed_agent_output(
        app,
        run_id="run-conflict",
        prediction_date=date(2026, 7, 13),
        agent_type="evidence",
        payload={"content": "# Completed actuals"},
        horizon_days=None,
    )

    with patch(
        "server.stages.run_delta",
        side_effect=FileExistsError("Delta output belongs to another pair"),
    ):
        response = client.post(
            "/stages/delta",
            json={"prediction_date": "2026-07-13", "run_id": "run-conflict"},
        )

    assert response.status_code == 409
    assert "another pair" in response.get_json()["error"]
