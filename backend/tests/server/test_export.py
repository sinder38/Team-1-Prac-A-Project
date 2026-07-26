"""Export: regenerate markdown artifacts from the DB (never write to real /data)."""

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from agents.delta.models import DeltaReport, WeekAccuracy
from server.db import export, repository as repo
from tests.server.conftest import (
    app_session,
    seed_agent_output,
    seed_llm_output,
    seed_runtime_run,
)


def _llm_payload(model_name: str) -> dict:
    return {
        "prediction_date": "2026-06-21",
        "model_name": model_name,
        "weekly_regime": "Uncertain",
        "confidence": "Medium",
        "spx_range": {"low": -1.2, "high": 1.5},
        "ndx_range": {"low": -0.5, "high": 2.0},
        "iwm_range": {"low": -1.0, "high": 1.2},
        "invalidation": "A dovish Fed reverses the cautious stance.",
        "plain_english": "The market is in a tug-of-war.",
        "supporting_evidence": ["Technicals bullish", "XLK seasonal strength"],
        "contradictions": ["Bullish technicals vs bearish June seasonality"],
        "agent_type": "llm",
    }


def _delta_payload() -> dict:
    report = DeltaReport(
        schema_version=2,
        prediction_week="vW25",
        actuals_week="W26",
        rows=[],
        missing_prediction_assets=[],
        missing_actual_assets=[],
        history=[
            WeekAccuracy(
                prediction_week="W25",
                actuals_week="W26",
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
    return asdict(report)


def test_post_export_stem_no_write(archive_client):
    """An archive week exports agents + the comparison + the human score."""
    resp = archive_client.post("/export", json={"stem": "W25", "write": False})
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["week"] == "W25"
    assert data["written"] == []  # write=False -> nothing written to disk
    kinds = {a["agent_type"] for a in data["artifacts"]}
    assert kinds == {
        "almanac",
        "macro",
        "technical",
        "evidence",
        "llm_comparison",
        "human_score",
    }
    for art in data["artifacts"]:
        assert art["markdown"].strip()

    # Archive weeks have no per-model LLM outputs stored, so no synthesis files.
    files = {a["filename"] for a in data["artifacts"]}
    assert f"llm_comparison_W25.md" in files
    assert f"human_score_W25.md" in files
    assert not any(f.startswith("synthesis_") for f in files)


def test_post_export_missing_run(archive_client):
    resp = archive_client.post("/export", json={"stem": "W99", "write": False})
    assert resp.status_code == 404


def test_post_export_requires_target(archive_client):
    resp = archive_client.post("/export", json={})
    assert resp.status_code == 400


def test_post_export_runtime_run_synthesis_and_comparison(app):
    """A live run with per-model LLM outputs exports synthesis + comparison."""
    pred = date(2026, 6, 21)
    seed_agent_output(
        app,
        run_id="run-x",
        prediction_date=pred,
        agent_type="almanac",
        payload={
            "prediction_date": "2026-06-21",
            "monthly_bias": "Bearish",
            "seasonal_bias": "Bearish",
            "thesis": "June midterm weakness.",
            "confidence": "Medium",
            "sectors": [],
            "agent_type": "almanac",
        },
    )
    seed_llm_output(
        app,
        run_id="run-x",
        prediction_date=pred,
        model_slug="gemma",
        payload=_llm_payload("Google Gemma 4 31B"),
    )
    seed_llm_output(
        app,
        run_id="run-x",
        prediction_date=pred,
        model_slug="laguna",
        payload=_llm_payload("Poolside Laguna M.1"),
    )

    with app.test_client() as c:
        resp = c.post("/export", json={"run_id": "run-x", "write": False})
    assert resp.status_code == 200
    data = json.loads(resp.data)
    files = {a["filename"] for a in data["artifacts"]}
    assert "synthesis_gemma_W25.txt" in files
    assert "synthesis_laguna_W25.txt" in files
    assert "llm_comparison_W25.md" in files
    # No human score was submitted for this live run.
    assert not any(f.startswith("human_score_") for f in files)

    synth = next(
        a["markdown"] for a in data["artifacts"] if a["filename"] == "synthesis_gemma_W25.txt"
    )
    assert "LLM Agent Output — Google Gemma 4 31B" in synth
    comparison = next(
        a["markdown"] for a in data["artifacts"] if a["filename"] == "llm_comparison_W25.md"
    )
    assert "Google Gemma 4 31B" in comparison
    assert "Poolside Laguna M.1" in comparison


def test_post_export_includes_final_prediction(app):
    """A runtime run with a stored final prediction exports the Team1 brief."""
    from datetime import date as _date

    from server.db import repository as repo
    from tests.server.conftest import app_session, seed_runtime_run

    seed_runtime_run(app, run_id="run-fp", prediction_date=_date(2026, 6, 21))
    report = {
        "week": "2026-W25",
        "form": {"regime": "Neutral-bullish."},
        "markdown": "# TEAM 1 2026-W25 CONSENSUS BRIEF — FILED: 21 JUN 2026\n\n## REGIME\n\nNeutral-bullish.\n",
    }
    with app_session(app) as session:
        run = repo.get_runtime_run(session, "run-fp")
        assert run is not None
        repo.upsert_final_prediction(session, run, report)

    with app.test_client() as c:
        resp = c.post("/export", json={"run_id": "run-fp", "write": False})
    assert resp.status_code == 200
    arts = json.loads(resp.data)["artifacts"]
    fp = next(a for a in arts if a["agent_type"] == "final_prediction")
    assert fp["filename"] == "prediction_2026-W25_Team1.md"
    assert "CONSENSUS BRIEF" in fp["markdown"]
    assert fp["markdown"].endswith("\n")

def test_post_export_includes_delta_report_from_sqlite(app):
    """The export endpoint renders a stored Delta report as Markdown."""
    prediction_date = date(2026, 6, 21)
    seed_runtime_run(app, run_id="run-delta", prediction_date=prediction_date)

    with app_session(app) as session:
        run = repo.get_runtime_run(session, "run-delta")
        assert run is not None
        repo.add_delta_report(
            session,
            run,
            prediction_week="vW25",
            schema_version=2,
            payload=_delta_payload(),
        )

    response = app.test_client().post(
        "/export", json={"run_id": "run-delta", "write": False}
    )

    assert response.status_code == 200
    artifacts = response.get_json()["artifacts"]
    delta = next(item for item in artifacts if item["agent_type"] == "delta")
    assert delta["filename"] == "delta_W25.md"
    assert "## Current-week summary" in delta["markdown"]
    assert "## Prescription for next sprint" in delta["markdown"]


def test_write_delta_report_to_markdown_file(app, tmp_path):
    """The Delta artifact is written under the QA directory."""
    prediction_date = date(2026, 6, 21)
    seed_runtime_run(app, run_id="run-delta-file", prediction_date=prediction_date)

    with app_session(app) as session:
        run = repo.get_runtime_run(session, "run-delta-file")
        assert run is not None
        repo.add_delta_report(
            session,
            run,
            prediction_week="vW25",
            schema_version=2,
            payload=_delta_payload(),
        )
        artifacts = export.build_run_artifacts(session, run)
        written = export.write_artifacts(artifacts, data_dir=tmp_path)

    assert str(tmp_path / "qa" / "delta_W25.md") in written
    assert (tmp_path / "qa" / "delta_W25.md").read_text(encoding="utf-8").startswith(
        "# delta_W25.md"
    )


def test_write_artifacts_to_tmp(archive_app, tmp_path):
    from server.db.context import db_session

    with archive_app.app_context():
        with db_session() as session:
            run = repo.get_archive_run(session, "W25")
            assert run is not None
            artifacts = export.build_run_artifacts(session, run)
            written = export.write_artifacts(artifacts, data_dir=tmp_path)

    # Paths may use / or \ depending on OS — compare basenames only.
    names = {Path(p).name for p in written}
    assert "almanac_agent_W25.md" in names
    assert "macro_agent_W25.md" in names
    assert "technical_agent_W25.md" in names
    assert "actuals_W25.md" in names
    assert "llm_comparison_W25.md" in names
    assert "human_score_W25.md" in names
    for subdir in ("almanac", "macro", "technical", "evidence", "llm", "human"):
        assert (tmp_path / subdir).is_dir()
