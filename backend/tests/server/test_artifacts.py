import json
import pytest
from pathlib import Path
from unittest.mock import patch

from server import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_get_almanac_found(client, tmp_path):
    artifact = {"monthly_bias": "Bullish", "horizon_days": 7}
    fake_path = tmp_path / "almanac_W25_run1_7d.json"
    fake_path.write_text(json.dumps(artifact))

    with patch("server.artifacts.artifact_path", return_value=fake_path):
        resp = client.get("/artifacts/almanac?run_id=run1&horizon_days=7&prediction_date=2026-06-18")
    assert resp.status_code == 200
    assert json.loads(resp.data)["monthly_bias"] == "Bullish"


def test_get_almanac_not_found(client, tmp_path):
    fake_path = tmp_path / "almanac_W25_run1_7d.json"  # does not exist
    with patch("server.artifacts.artifact_path", return_value=fake_path):
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
    fake_path = tmp_path / "evidence_W25_run1.json"
    fake_path.write_text(json.dumps(artifact))
    with patch("server.artifacts.artifact_path", return_value=fake_path):
        resp = client.get("/artifacts/evidence?run_id=run1&prediction_date=2026-06-18")
    assert resp.status_code == 200
    assert json.loads(resp.data)["week"] == "W25"


def test_get_llm_found(client, tmp_path):
    artifact = {"weekly_regime": "Bullish", "horizon_days": 7}
    fake_path = tmp_path / "llm_nemotron_W25_run1_7d.json"
    fake_path.write_text(json.dumps(artifact))
    with patch("server.artifacts.artifact_path", return_value=fake_path):
        resp = client.get("/artifacts/llm?run_id=run1&model=nemotron&horizon_days=7&prediction_date=2026-06-18")
    assert resp.status_code == 200


def test_get_llm_missing_model(client):
    resp = client.get("/artifacts/llm?run_id=run1&horizon_days=7")
    assert resp.status_code == 400


def test_get_runs(client, tmp_path):
    # Create two artifacts for W25 with different run_ids
    (tmp_path / "almanac").mkdir()
    (tmp_path / "almanac" / "almanac_W25_run1_7d.json").write_text("{}")
    (tmp_path / "almanac" / "almanac_W25_run2_7d.json").write_text("{}")
    (tmp_path / "almanac" / "almanac_W24_other_7d.json").write_text("{}")  # different week

    # Add LLM artifacts to test LLM filename pattern matching
    (tmp_path / "llm").mkdir()
    (tmp_path / "llm" / "llm_nemotron_W25_run1_7d.json").write_text("{}")  # same run_id as almanac
    (tmp_path / "llm" / "llm_nemotron_W25_run3_7d.json").write_text("{}")  # new run_id

    with patch("server.artifacts.OUTPUTS_ROOT", tmp_path):
        resp = client.get("/artifacts/runs?prediction_date=2026-06-18")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert set(data["run_ids"]) == {"run1", "run2", "run3"}
    assert data["week"] == "W25"


def test_get_runs_missing_date(client):
    resp = client.get("/artifacts/runs")
    assert resp.status_code == 400
