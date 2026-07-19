import json

import pytest

from agents import db
from agents.db import save_agent_artifact, save_llm_artifact, save_human_score
from server import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTS_DATABASE_PATH", str(tmp_path / "agents_test.db"))
    monkeypatch.setenv("LLM_DATABASE_PATH", str(tmp_path / "llm_test.db"))
    monkeypatch.setenv("HUMAN_DATABASE_PATH", str(tmp_path / "human_test.db"))
    monkeypatch.setattr(db, "HUMAN_MD_DIR", tmp_path / "human")
    (tmp_path / "human").mkdir()
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_get_almanac_found(client):
    artifact = {"monthly_bias": "Bullish", "horizon_days": 7}
    save_agent_artifact(agent_type="almanac", week_stem="W25", run_id="run1", horizon_days=7, data=artifact,
                  prediction_date="2026-06-18",)
    resp = client.get("/artifacts/almanac?run_id=run1&horizon_days=7&prediction_date=2026-06-18")
    assert resp.status_code == 200
    assert json.loads(resp.data)["monthly_bias"] == "Bullish"


def test_get_almanac_not_found(client):
    resp = client.get("/artifacts/almanac?run_id=run1&horizon_days=7&prediction_date=2026-06-18")
    assert resp.status_code == 404


def test_get_almanac_missing_run_id(client):
    resp = client.get("/artifacts/almanac?horizon_days=7")
    assert resp.status_code == 400


def test_get_almanac_missing_horizon(client):
    resp = client.get("/artifacts/almanac?run_id=run1")
    assert resp.status_code == 400


def test_get_evidence_no_horizon(client):
    artifact = {"week": "W25", "content": "# data"}
    save_agent_artifact(agent_type="evidence", week_stem="W25", run_id="run1", data=artifact,
                        prediction_date="2026-06-18")
    resp = client.get("/artifacts/evidence?run_id=run1&prediction_date=2026-06-18")
    assert resp.status_code == 200
    assert json.loads(resp.data)["week"] == "W25"


def test_get_llm_found(client):
    artifact = {"weekly_regime": "Bullish", "horizon_days": 7}
    save_llm_artifact(
        week_stem="W25",
        run_id="run1",
        model="nemotron",
        horizon_days=7,
        data=artifact,
        prediction_date="2026-06-18",
    )
    resp = client.get("/artifacts/llm?run_id=run1&model=nemotron&horizon_days=7&prediction_date=2026-06-18")
    assert resp.status_code == 200


def test_get_llm_missing_model(client):
    resp = client.get("/artifacts/llm?run_id=run1&horizon_days=7")
    assert resp.status_code == 400


def test_get_runs(client, tmp_path):
    # Create two artifacts for W25 with different run_ids
    save_agent_artifact(agent_type="almanac", week_stem="W25", run_id="run1", horizon_days=7, data={})
    save_agent_artifact(agent_type="almanac", week_stem="W25", run_id="run2", horizon_days=7, data={})
    save_agent_artifact(agent_type="almanac", week_stem="W24", run_id="other", horizon_days=7, data={})  # different week

    # Add LLM artifacts to test LLM filename pattern matching
    save_llm_artifact(week_stem="W25", run_id="run1", horizon_days=7, model="nemotron", data={})
    save_llm_artifact(week_stem="W25", run_id="run3", horizon_days=7, model="nemotron", data={})

    resp = client.get("/artifacts/runs?prediction_date=2026-06-18")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert set(data["run_ids"]) == {"run1", "run2", "run3"}
    assert data["week"] == "W25"


def test_get_runs_missing_date(client):
    resp = client.get("/artifacts/runs")
    assert resp.status_code == 400


def test_get_runs_empty_when_no_outputs_dir(client):
    resp = client.get("/artifacts/runs?prediction_date=2026-06-18")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["run_ids"] == []

    def test_get_human_score_found(client):
        save_human_score(week_stem="W25", data="# Human Score — Week 25\n")
        resp = client.get("/artifacts/human-score?stem=W25")
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["week"] == "W25"
        assert "Week 25" in body["data"]

    def test_get_human_score_by_prediction_date(client):
        save_human_score(week_stem="W25", data="# Human Score — Week 25\n")
        resp = client.get("/artifacts/human-score?prediction_date=2026-06-18")
        assert resp.status_code == 200
        assert json.loads(resp.data)["week"] == "W25"

    def test_get_human_score_not_found(client):
        resp = client.get("/artifacts/human-score?stem=W25")
        assert resp.status_code == 404

