import json
import pytest
from datetime import date
from pathlib import Path

from server.utils import parse_date, artifact_path, load_artifact, err


def test_parse_date_valid():
    assert parse_date("2026-06-18") == date(2026, 6, 18)


def test_parse_date_invalid():
    with pytest.raises(ValueError):
        parse_date("not-a-date")


def test_artifact_path_almanac():
    p = artifact_path("almanac", "W25", "run1", horizon_days=7)
    assert p.name == "almanac_W25_run1_7d.json"
    assert "almanac" in str(p)


def test_artifact_path_evidence():
    p = artifact_path("evidence", "W25", "run1")
    assert p.name == "evidence_W25_run1.json"


def test_artifact_path_llm():
    p = artifact_path("llm", "W25", "run1", model="nemotron", horizon_days=7)
    assert p.name == "llm_nemotron_W25_run1_7d.json"


def test_load_artifact_found(tmp_path):
    f = tmp_path / "test.json"
    f.write_text(json.dumps({"key": "val"}))
    assert load_artifact(f) == {"key": "val"}


def test_load_artifact_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_artifact(tmp_path / "nope.json")


def test_err_shape():
    import flask
    app = flask.Flask(__name__)
    with app.app_context():
        response, status = err("bad input", 400)
        assert status == 400
        assert json.loads(response.data) == {"error": "bad input"}
