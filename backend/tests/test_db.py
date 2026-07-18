import json
import os
from datetime import date

import pytest

from agents import db


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path, monkeypatch):
    path = tmp_path / "predictions.db"
    monkeypatch.setenv("DATABASE_PATH", str(path))
    yield path


def test_save_and_load_roundtrip():
    payload = {"monthly_bias": "Bullish", "prediction_date": "2026-06-16"}
    db.save_artifact(
        agent_type="almanac",
        week_stem="W25",
        run_id="run1",
        horizon_days=7,
        data=payload,
        prediction_date=date(2026, 6, 16),
    )
    loaded = db.load_artifact(
        agent_type="almanac", week_stem="W25", run_id="run1", horizon_days=7
    )
    assert loaded["monthly_bias"] == "Bullish"


def test_upsert_overwrites():
    db.save_artifact(
        agent_type="almanac", week_stem="W25", run_id="run1",
        horizon_days=7, data={"v": 1},
    )
    db.save_artifact(
        agent_type="almanac", week_stem="W25", run_id="run1",
        horizon_days=7, data={"v": 2},
    )
    assert db.load_artifact(
        agent_type="almanac", week_stem="W25", run_id="run1", horizon_days=7
    )["v"] == 2


def test_evidence_without_horizon():
    db.save_artifact(
        agent_type="evidence", week_stem="W25", run_id="run1",
        data={"week": "W25", "content": "# hi"},
    )
    loaded = db.load_artifact(
        agent_type="evidence", week_stem="W25", run_id="run1"
    )
    assert loaded["week"] == "W25"


def test_llm_with_model():
    db.save_artifact(
        agent_type="llm", week_stem="W25", run_id="run1",
        horizon_days=7, model="nemotron", data={"weekly_regime": "Bullish"},
    )
    loaded = db.load_artifact(
        agent_type="llm", week_stem="W25", run_id="run1",
        horizon_days=7, model="nemotron",
    )
    assert loaded["weekly_regime"] == "Bullish"


def test_list_run_ids():
    db.save_artifact(
        agent_type="almanac", week_stem="W25", run_id="run1",
        horizon_days=7, data={},
    )
    db.save_artifact(
        agent_type="almanac", week_stem="W25", run_id="run2",
        horizon_days=7, data={},
    )
    db.save_artifact(
        agent_type="llm", week_stem="W25", run_id="run3",
        horizon_days=7, model="nemotron", data={},
    )
    db.save_artifact(
        agent_type="almanac", week_stem="W24", run_id="other",
        horizon_days=7, data={},
    )
    assert db.list_run_ids("W25") == ["run1", "run2", "run3"]


def test_missing_raises():
    with pytest.raises(FileNotFoundError):
        db.load_artifact(
            agent_type="almanac", week_stem="W25", run_id="missing", horizon_days=7
        )