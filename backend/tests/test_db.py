from datetime import date

import pytest

from agents import db


@pytest.fixture(autouse=True)
def _tmp_dbs(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTS_DATABASE_PATH", str(tmp_path / "agents.db"))
    monkeypatch.setenv("LLM_DATABASE_PATH", str(tmp_path / "llm.db"))
    monkeypatch.setenv("HUMAN_DATABASE_PATH", str(tmp_path / "human.db"))
    monkeypatch.setattr(db, "HUMAN_MD_DIR", tmp_path / "human")
    (tmp_path / "human").mkdir()
    yield


def test_save_and_load_roundtrip():
    payload = {"monthly_bias": "Bullish", "prediction_date": "2026-06-16"}
    db.save_agent_artifact(
        agent_type="almanac",
        week_stem="W25",
        run_id="run1",
        horizon_days=7,
        data=payload,
        prediction_date=date(2026, 6, 16),
    )
    loaded = db.load_agent_artifact(
        agent_type="almanac", week_stem="W25", run_id="run1", horizon_days=7
    )
    assert loaded["monthly_bias"] == "Bullish"


def test_upsert_overwrites():
    db.save_agent_artifact(
        agent_type="almanac",
        week_stem="W25",
        run_id="run1",
        horizon_days=7,
        data={"v": 1},
    )
    db.save_agent_artifact(
        agent_type="almanac",
        week_stem="W25",
        run_id="run1",
        horizon_days=7,
        data={"v": 2},
    )
    assert (
            db.load_agent_artifact(
                agent_type="almanac", week_stem="W25", run_id="run1", horizon_days=7
            )["v"]
            == 2
    )


def test_evidence_without_horizon():
    db.save_agent_artifact(
        agent_type="evidence",
        week_stem="W25",
        run_id="run1",
        data={"week": "W25", "content": "# hi"},
    )
    loaded = db.load_agent_artifact(
        agent_type="evidence", week_stem="W25", run_id="run1"
    )
    assert loaded["week"] == "W25"


def test_llm_with_model():
    db.save_llm_artifact(
        week_stem="W25",
        run_id="run1",
        horizon_days=7,
        model="nemotron",
        data={"weekly_regime": "Bullish"},
    )
    loaded = db.load_llm_artifact(
        week_stem="W25",
        run_id="run1",
        horizon_days=7,
        model="nemotron",
    )
    assert loaded["weekly_regime"] == "Bullish"


def test_list_run_ids():
    db.save_agent_artifact(
        agent_type="almanac", week_stem="W25", run_id="run1", horizon_days=7, data={}
    )
    db.save_agent_artifact(
        agent_type="almanac", week_stem="W25", run_id="run2", horizon_days=7, data={}
    )
    db.save_llm_artifact(
        week_stem="W25",
        run_id="run3",
        horizon_days=7,
        model="nemotron",
        data={},
    )
    db.save_agent_artifact(
        agent_type="almanac", week_stem="W24", run_id="other", horizon_days=7, data={}
    )
    assert db.list_run_ids("W25") == ["run1", "run2", "run3"]


def test_missing_raises():
    with pytest.raises(FileNotFoundError):
        db.load_agent_artifact(
            agent_type="almanac", week_stem="W25", run_id="missing", horizon_days=7
        )


def test_agent_artifact_exists():
    assert (
            db.agent_artifact_exists(
                agent_type="almanac", week_stem="W25", run_id="run1", horizon_days=7
            )
            is False
    )
    db.save_agent_artifact(
        agent_type="almanac", week_stem="W25", run_id="run1", horizon_days=7, data={}
    )
    assert (
            db.agent_artifact_exists(
                agent_type="almanac", week_stem="W25", run_id="run1", horizon_days=7
            )
            is True
    )


def test_ingest_human_score_skips_if_missing():
    assert db.ingest_human_score_md("W25") is False


def test_ingest_human_score_stores_md():
    (db.HUMAN_MD_DIR / "human_score_W25.md").write_text(
        "# Human Score — Week 25\n", encoding="utf-8"
    )
    assert db.ingest_human_score_md("W25") is True
    assert "Week 25" in db.load_human_score(week_stem="W25")
