import json
from datetime import date

from tests.server.conftest import seed_agent_output, seed_llm_output, seed_runtime_run


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
    assert by_week["2026-W28"]["source"] == "run"
    assert by_week["2026-W28"]["created_at"]
    # Multiple pipeline runs per week are listed separately (not collapsed).
    w29_runs = {w["run_id"] for w in weeks if w["week"] == "2026-W29"}
    assert w29_runs == {"run-bbb", "run-ccc"}


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
    assert data["finalPrediction"] is not None
    assert data["finalPrediction"]["form"]["assets"]["spx"]["direction"]
    assert data["finalPrediction"]["markdown"]


def test_get_archive_final_prediction_w29(archive_client):
    resp = archive_client.get("/artifacts/archive?stem=W29")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    fp = data["finalPrediction"]
    assert fp is not None
    assert "Bearish" in fp["form"]["regime"]
    assert "|" not in fp["form"]["regime"]  # asset table must not leak into regime
    assert fp["form"]["assets"]["ndx"]["direction"] == "DOWN"
    assert fp["form"]["assets"]["vix"]["range"] == "17–28 range"
    assert fp["form"]["evidence1"]
    assert "INVALIDATION" in fp["markdown"]


def test_get_archive_final_prediction_w28_regime_clean(archive_client):
    resp = archive_client.get("/artifacts/archive?stem=W28")
    assert resp.status_code == 200
    regime = json.loads(resp.data)["finalPrediction"]["form"]["regime"]
    assert "Neutral-Bullish" in regime
    assert "| Asset" not in regime
    assert "**" not in regime


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


def test_runtime_human_score_roundtrip(client, app):
    seed_runtime_run(app, run_id="run-hsr-1", prediction_date=date(2026, 7, 20))
    report = {
        "week": "2026-W30",
        "predictionDate": "2026-07-20",
        "total": 3,
        "consensus": "Neutral",
        "form": {
            "humanCall": "Neutral-Bullish",
            "confidence": "Medium",
            "scores": {"technical": 1, "almanac": 1, "macro": 1, "aiAgreement": 0, "wildCard": 0},
        },
    }

    missing = client.get("/artifacts/human-score?run_id=run-hsr-1")
    assert missing.status_code == 404

    saved = client.post(
        "/artifacts/human-score",
        json={"run_id": "run-hsr-1", "report": report},
    )
    assert saved.status_code == 200

    loaded = client.get("/artifacts/human-score?run_id=run-hsr-1")
    assert loaded.status_code == 200
    data = json.loads(loaded.data)
    assert data["form"]["humanCall"] == "Neutral-Bullish"
    assert data["total"] == 3


def test_runtime_llm_comparison_from_outputs(client, app):
    seed_llm_output(
        app,
        run_id="run-llm-1",
        prediction_date=date(2026, 7, 20),
        model_slug="nemotron",
        payload={
            "model_name": "NVIDIA Nemotron",
            "weekly_regime": "Bearish",
            "confidence": "Medium",
            "spx_range": {"low": -2.0, "high": 0.5},
            "ndx_range": {"low": -3.0, "high": 0.0},
            "iwm_range": {"low": -2.0, "high": 0.5},
            "supporting_evidence": ["a"],
            "contradictions": ["b"],
            "invalidation": "c",
            "plain_english": "Cautious week.",
            "horizon_days": 7,
        },
    )

    missing = client.get("/artifacts/llm-comparison?run_id=missing")
    assert missing.status_code == 404

    resp = client.get("/artifacts/llm-comparison?run_id=run-llm-1")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["source"] == "outputs"
    assert len(data["models"]) == 1
    assert data["models"][0]["slug"] == "nemotron"
    assert data["models"][0]["data"]["weekly_regime"] == "Bearish"


def test_runtime_final_prediction_roundtrip(client, app, tmp_path, monkeypatch):
    seed_runtime_run(app, run_id="run-fp-1", prediction_date=date(2026, 7, 20))
    report = {
        "week": "2026-W30",
        "predictionDate": "2026-07-20",
        "form": {
            "regime": "Bearish with medium uncertainty.",
            "assets": {
                "spx": {"direction": "FLAT-DOWN", "range": "-2% to +1%", "confidence": "MEDIUM"},
            },
            "leadingSector": "Energy",
            "laggingSector": "Tech",
            "evidence1": "a",
            "evidence2": "b",
            "evidence3": "c",
            "contradiction": "d",
            "wildCard": "e",
            "invalidation": "f",
        },
        "markdown": "# TEAM 1 2026-W30 CONSENSUS BRIEF\n\n## REGIME\n\nBearish.\n",
    }

    missing = client.get("/artifacts/final-prediction?run_id=run-fp-1")
    assert missing.status_code == 404

    data_dir = tmp_path / "data"
    monkeypatch.setattr("agents.paths.DATA_DIR", data_dir)

    saved = client.post(
        "/artifacts/final-prediction",
        json={"run_id": "run-fp-1", "report": report},
    )
    assert saved.status_code == 200
    body = json.loads(saved.data)
    assert body["ok"] is True
    # Submission is DB-only: no markdown is written to disk here.
    assert "path" not in body
    assert not (data_dir / "final prediction").exists()

    # The brief markdown is produced on demand by POST /export.
    export = client.post("/export", json={"run_id": "run-fp-1", "write": False})
    assert export.status_code == 200
    arts = json.loads(export.data)["artifacts"]
    fp = next(a for a in arts if a["agent_type"] == "final_prediction")
    assert fp["filename"] == "prediction_2026-W30_Team1.md"
    assert "CONSENSUS BRIEF" in fp["markdown"]

    loaded = client.get("/artifacts/final-prediction?run_id=run-fp-1")
    assert loaded.status_code == 200
    data = json.loads(loaded.data)
    assert data["form"]["regime"] == "Bearish with medium uncertainty."
    assert data["week"] == "2026-W30"

    # Same run may re-submit; a second run in the same week may not.
    again = client.post(
        "/artifacts/final-prediction",
        json={"run_id": "run-fp-1", "report": report},
    )
    assert again.status_code == 200

    seed_runtime_run(app, run_id="run-fp-2", prediction_date=date(2026, 7, 20))
    conflict = client.post(
        "/artifacts/final-prediction",
        json={"run_id": "run-fp-2", "report": report},
    )
    assert conflict.status_code == 409
