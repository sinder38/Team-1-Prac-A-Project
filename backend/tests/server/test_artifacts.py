import json
import pytest

from agents.db import save_artifact
from server import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_get_almanac_found(client, tmp_path):
    artifact = {"monthly_bias": "Bullish", "horizon_days": 7}
    save_artifact(agent_type="almanac", week_stem="W25", run_id="run1", horizon_days=7, data=artifact)
    resp = client.get("/artifacts/almanac?run_id=run1&horizon_days=7&prediction_date=2026-06-18")
    assert resp.status_code == 200
    assert json.loads(resp.data)["monthly_bias"] == "Bullish"


def test_get_almanac_not_found(client, tmp_path):
    resp = client.get("/artifacts/almanac?run_id=run1&horizon_days=7&prediction_date=2026-06-18")
    assert resp.status_code == 404


def test_get_almanac_missing_run_id(client):
    resp = client.get("/artifacts/almanac?horizon_days=7")
    assert resp.status_code == 400


def test_get_almanac_missing_horizon(client):
    resp = client.get("/artifacts/almanac?run_id=run1")
    assert resp.status_code == 400


def test_get_evidence_no_horizon(client, tmp_path):
    artifact = {"week": "W25", "content": "# data"}
    save_artifact(agent_type="evidence", week_stem="W25", run_id="run1", data=artifact)
    resp = client.get("/artifacts/evidence?run_id=run1&prediction_date=2026-06-18")
    assert resp.status_code == 200
    assert json.loads(resp.data)["week"] == "W25"


def test_get_llm_found(client, tmp_path):
    artifact = {"weekly_regime": "Bullish", "horizon_days": 7}
    save_artifact(
        agent_type="llm",
        week_stem="W25",
        run_id="run1",
        horizon_days=7,
        model="nemotron",
        data=artifact,
    )
    resp = client.get("/artifacts/llm?run_id=run1&model=nemotron&horizon_days=7&prediction_date=2026-06-18")
    assert resp.status_code == 200


def test_get_llm_missing_model(client):
    resp = client.get("/artifacts/llm?run_id=run1&horizon_days=7")
    assert resp.status_code == 400


def test_get_runs(client, tmp_path):
    # Create two artifacts for W25 with different run_ids
    save_artifact(agent_type="almanac", week_stem="W25", run_id="run1", horizon_days=7, data={})
    save_artifact(agent_type="almanac", week_stem="W25", run_id="run2", horizon_days=7, data={})
    save_artifact(agent_type="almanac", week_stem="W24", run_id="other", horizon_days=7, data={})  # different week

    # Add LLM artifacts to test LLM filename pattern matching
    save_artifact(agent_type="llm", week_stem="W25", run_id="run1", horizon_days=7, model="nemotron", data={})
    save_artifact(agent_type="llm", week_stem="W25", run_id="run3", horizon_days=7, model="nemotron", data={})

    resp = client.get("/artifacts/runs?prediction_date=2026-06-18")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert set(data["run_ids"]) == {"run1", "run2", "run3"}
    assert data["week"] == "W25"


def test_get_runs_missing_date(client):
    resp = client.get("/artifacts/runs")
    assert resp.status_code == 400


def test_get_runs_empty_when_no_rows(client, tmp_path):
    resp = client.get("/artifacts/runs?prediction_date=2026-06-18")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["run_ids"] == []
