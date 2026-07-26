import json
from datetime import date

from server.db import repository as repo
from tests.server.conftest import (
    app_session,
    seed_agent_output,
    seed_llm_output,
    seed_runtime_run,
)


def test_get_almanac_found(client, app):
    seed_agent_output(
        app,
        run_id="run1",
        prediction_date=date(2026, 6, 18),
        agent_type="almanac",
        payload={"monthly_bias": "Bullish", "horizon_days": 7},
    )
    resp = client.get(
        "/artifacts/almanac?run_id=run1&horizon_days=7&prediction_date=2026-06-18"
    )
    assert resp.status_code == 200
    assert json.loads(resp.data)["monthly_bias"] == "Bullish"


def test_get_almanac_not_found(client):
    resp = client.get(
        "/artifacts/almanac?run_id=run1&horizon_days=7&prediction_date=2026-06-18"
    )
    assert resp.status_code == 404


def test_get_almanac_missing_run_id(client):
    resp = client.get("/artifacts/almanac?horizon_days=7")
    assert resp.status_code == 400


def test_get_almanac_missing_horizon(client):
    resp = client.get("/artifacts/almanac?run_id=run1")
    assert resp.status_code == 400


def test_get_evidence_no_horizon(client, app):
    seed_agent_output(
        app,
        run_id="run1",
        prediction_date=date(2026, 6, 18),
        agent_type="evidence",
        payload={"week": "W25", "content": "# data"},
        horizon_days=None,
    )
    resp = client.get("/artifacts/evidence?run_id=run1&prediction_date=2026-06-18")
    assert resp.status_code == 200
    assert json.loads(resp.data)["week"] == "W25"


def test_get_llm_found(client, app):
    seed_llm_output(
        app,
        run_id="run1",
        prediction_date=date(2026, 6, 18),
        model_slug="nemotron",
        payload={"weekly_regime": "Bullish", "horizon_days": 7},
    )
    query = (
        "/artifacts/llm?run_id=run1&model=nemotron"
        "&horizon_days=7&prediction_date=2026-06-18"
    )
    resp = client.get(query)
    assert resp.status_code == 200
    assert json.loads(resp.data)["weekly_regime"] == "Bullish"


def test_get_llm_missing_model(client):
    resp = client.get("/artifacts/llm?run_id=run1&horizon_days=7")
    assert resp.status_code == 400


def test_get_runs(client, app):
    # Three runtime runs in week W25 (2026-06-18) plus one in a different week.
    for run_id in ("run1", "run2", "run3"):
        seed_runtime_run(app, run_id=run_id, prediction_date=date(2026, 6, 18))
    seed_runtime_run(app, run_id="other", prediction_date=date(2026, 6, 8))  # W24

    resp = client.get("/artifacts/runs?prediction_date=2026-06-18")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert set(data["run_ids"]) == {"run1", "run2", "run3"}
    assert data["week"] == "W25"


def test_get_runs_missing_date(client):
    resp = client.get("/artifacts/runs")
    assert resp.status_code == 400


def test_get_runs_empty_when_no_runs(client):
    resp = client.get("/artifacts/runs?prediction_date=2026-06-18")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["run_ids"] == []


def test_run_status_tracks_persisted_pipeline_progress(client, app):
    prediction_date = date(2026, 6, 18)
    run_id = "partial-run"
    seed_runtime_run(app, run_id=run_id, prediction_date=prediction_date)

    def completed_stages() -> int:
        response = client.get(f"/artifacts/run-status?run_id={run_id}")
        assert response.status_code == 200
        return response.get_json()["completed_stages"]

    assert completed_stages() == 0

    for agent_type in ("almanac", "macro", "technical"):
        seed_agent_output(
            app,
            run_id=run_id,
            prediction_date=prediction_date,
            agent_type=agent_type,
            payload={},
        )
    assert completed_stages() == 2

    seed_llm_output(
        app,
        run_id=run_id,
        prediction_date=prediction_date,
        model_slug="llama",
        payload={"model_name": "Llama"},
    )
    assert completed_stages() == 3

    with app_session(app) as session:
        run = repo.get_runtime_run(session, run_id)
        assert run is not None
        repo.add_delta_report(
            session,
            run,
            prediction_week="vW24",
            schema_version=2,
            payload={"schema_version": 2, "prediction_week": "vW24"},
        )
    assert completed_stages() == 4

    with app_session(app) as session:
        run = repo.get_runtime_run(session, run_id)
        assert run is not None
        repo.upsert_human_score(session, run, {})
    assert completed_stages() == 5


def test_run_status_rejects_missing_or_unknown_run(client):
    missing = client.get("/artifacts/run-status")
    assert missing.status_code == 400

    unknown = client.get("/artifacts/run-status?run_id=missing")
    assert unknown.status_code == 404


def test_list_weeks_across_stems(client, app):
    # W28 run, then two W29 runs; the newest (by created_at) wins for its week.
    seed_runtime_run(app, run_id="run-aaa", prediction_date=date(2026, 7, 10))  # W28
    seed_runtime_run(app, run_id="run-bbb", prediction_date=date(2026, 7, 16))  # W29
    seed_runtime_run(app, run_id="run-ccc", prediction_date=date(2026, 7, 16))  # W29 newer

    resp = client.get("/artifacts/weeks")
    assert resp.status_code == 200
    weeks = json.loads(resp.data)["weeks"]
    by_week = {w["week"]: w for w in weeks}
    assert "2026-W28" in by_week
    assert "2026-W29" in by_week
    assert by_week["2026-W28"]["run_id"] == "run-aaa"
    assert by_week["2026-W28"]["prediction_date"] == "2026-07-10"
    assert by_week["2026-W29"]["run_id"] == "run-ccc"
    assert by_week["2026-W28"]["source"] == "run"


def test_list_weeks_empty(client):
    resp = client.get("/artifacts/weeks")
    assert resp.status_code == 200
    assert json.loads(resp.data)["weeks"] == []


def test_list_weeks_includes_archive(archive_client):
    resp = archive_client.get("/artifacts/weeks")
    assert resp.status_code == 200
    weeks = json.loads(resp.data)["weeks"]
    assert any(w["source"] == "archive" for w in weeks)
    assert any(w["week"] == "2026-W25" for w in weeks)


def test_get_archive_week(archive_client):
    resp = archive_client.get("/artifacts/archive?stem=W25")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["stem"] == "W25"
    assert data["almanac"] is not None
    assert "ALMANAC SEASONAL BIAS" in data["almanac"]["rawData"]
    assert data["llmComparison"] is not None
    assert len(data["llmComparison"]["models"]) >= 1
    assert data["llmComparison"]["models"][0]["evidence"]


def test_get_archive_missing(archive_client):
    resp = archive_client.get("/artifacts/archive?stem=W99")
    assert resp.status_code == 404


def test_get_human_score_w25(archive_client):
    resp = archive_client.get("/artifacts/human-score?stem=W25")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    # rawMarkdown is intentionally dropped by the structured store; assert the
    # structured fields instead.
    assert data["form"]["humanCall"] == "Neutral-Bullish"
    assert data["form"]["confidence"] == "Medium"
    assert data["form"]["scores"]["technical"] == 1
    assert data["form"]["scores"]["almanac"] == -1
    assert data["total"] == 2
    assert "rawMarkdown" not in data


def test_get_human_score_missing(archive_client):
    resp = archive_client.get("/artifacts/human-score?stem=W99")
    assert resp.status_code == 404
