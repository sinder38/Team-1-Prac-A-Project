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


def test_get_runs_empty_when_no_outputs_dir(client, tmp_path):
    nonexistent = tmp_path / "nonexistent"
    with patch("server.artifacts.OUTPUTS_ROOT", nonexistent):
        resp = client.get("/artifacts/runs?prediction_date=2026-06-18")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["run_ids"] == []


def test_list_weeks_across_stems(client, tmp_path):
    import os
    import time

    (tmp_path / "almanac").mkdir()
    (tmp_path / "almanac" / "almanac_W28_run-aaa_7d.json").write_text(
        json.dumps({"prediction_date": "2026-07-10"})
    )
    older = tmp_path / "almanac" / "almanac_W29_run-bbb_7d.json"
    newer = tmp_path / "almanac" / "almanac_W29_run-ccc_7d.json"
    older.write_text(json.dumps({"prediction_date": "2026-07-16"}))
    newer.write_text(json.dumps({"prediction_date": "2026-07-16"}))
    # Latest run is by mtime, not lexicographic run_id.
    now = time.time()
    os.utime(older, (now - 10, now - 10))
    os.utime(newer, (now, now))

    with patch("server.archive.OUTPUTS_ROOT", tmp_path), \
         patch("server.utils.OUTPUTS_ROOT", tmp_path), \
         patch("server.archive.list_archive_weeks", return_value=[]):
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


def test_list_weeks_empty(client, tmp_path):
    with patch("server.archive.OUTPUTS_ROOT", tmp_path / "missing"), \
         patch("server.archive.list_archive_weeks", return_value=[]):
        resp = client.get("/artifacts/weeks")
    assert resp.status_code == 200
    assert json.loads(resp.data)["weeks"] == []


def test_list_weeks_includes_archive(client, tmp_path, monkeypatch):
    from server import archive as archive_mod

    monkeypatch.setattr(
        archive_mod,
        "list_archive_weeks",
        lambda: [
            {
                "week": "2026-W25",
                "stem": "W25",
                "prediction_date": "2026-06-21",
                "run_id": None,
                "source": "archive",
            }
        ],
    )
    with patch("server.archive.OUTPUTS_ROOT", tmp_path / "missing"):
        resp = client.get("/artifacts/weeks")
    assert resp.status_code == 200
    weeks = json.loads(resp.data)["weeks"]
    assert any(w["week"] == "2026-W25" and w["source"] == "archive" for w in weeks)


def test_get_archive_week(client):
    resp = client.get("/artifacts/archive?stem=W25")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["stem"] == "W25"
    assert data["almanac"] is not None
    assert "ALMANAC SEASONAL BIAS" in data["almanac"]["rawData"]
    assert data["llmComparison"] is not None
    assert len(data["llmComparison"]["models"]) >= 1
    assert data["llmComparison"]["models"][0]["evidence"]


def test_get_archive_missing(client):
    resp = client.get("/artifacts/archive?stem=W99")
    assert resp.status_code == 404


def test_get_human_score_w25(client):
    resp = client.get("/artifacts/human-score?stem=W25")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["form"]["humanCall"] == "Neutral-Bullish"
    assert data["form"]["confidence"] == "Medium"
    assert data["form"]["scores"]["technical"] == 1
    assert data["form"]["scores"]["almanac"] == -1
    assert data["total"] == 2
    assert "Human Score Analyst Output" in data["rawMarkdown"]


def test_get_human_score_missing(client):
    resp = client.get("/artifacts/human-score?stem=W99")
    assert resp.status_code == 404
