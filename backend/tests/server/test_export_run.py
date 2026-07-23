import json
from datetime import date
from pathlib import Path

import pytest

from server.export_run import export_run_to_data


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_export_run_writes_markdown_for_present_agents(tmp_path):
    outputs = tmp_path / "outputs"
    data = tmp_path / "data"
    pred = date(2026, 6, 18)
    stem = "W25"
    run_id = "run1"
    horizon = 7

    _write_json(
        outputs / "almanac" / f"almanac_{stem}_{run_id}_{horizon}d.json",
        {
            "prediction_date": pred.isoformat(),
            "monthly_bias": "Bullish",
            "seasonal_bias": "Bearish",
            "confidence": "Medium",
            "thesis": "Test thesis",
            "weekly_pattern": "",
            "sector_signals": [],
        },
    )
    _write_json(
        outputs / "evidence" / f"evidence_{stem}_{run_id}.json",
        {
            "prediction_date": pred.isoformat(),
            "week": stem,
            "content": "# W25 actuals\n",
        },
    )

    written = export_run_to_data(
        pred,
        run_id,
        horizon,
        outputs_root=outputs,
        data_root=data,
    )

    assert any(p.endswith(f"almanac/almanac_agent_{stem}.md") for p in written)
    assert any(p.endswith(f"evidence/actuals_{stem}.md") for p in written)
    assert (data / "almanac" / f"almanac_agent_{stem}.md").exists()
    assert (data / "evidence" / f"actuals_{stem}.md").exists()
    assert "Test thesis" in (data / "almanac" / f"almanac_agent_{stem}.md").read_text(
        encoding="utf-8"
    )


def test_export_run_empty_when_no_artifacts(tmp_path):
    written = export_run_to_data(
        date(2026, 6, 18),
        "run-missing",
        7,
        outputs_root=tmp_path / "outputs",
        data_root=tmp_path / "data",
    )
    assert written == []


def test_export_overwrites_same_week_slot(tmp_path):
    """Archive paths are week-scoped; a second run export replaces the first."""
    outputs = tmp_path / "outputs"
    data = tmp_path / "data"
    pred = date(2026, 6, 18)
    stem = "W25"
    payload = {
        "prediction_date": pred.isoformat(),
        "monthly_bias": "Bullish",
        "seasonal_bias": "Bearish",
        "confidence": "Medium",
        "thesis": "first",
        "weekly_pattern": "",
        "sector_signals": [],
    }
    _write_json(outputs / "almanac" / f"almanac_{stem}_runA_7d.json", payload)
    export_run_to_data(pred, "runA", 7, outputs_root=outputs, data_root=data)

    payload["thesis"] = "second"
    _write_json(outputs / "almanac" / f"almanac_{stem}_runB_7d.json", payload)
    export_run_to_data(pred, "runB", 7, outputs_root=outputs, data_root=data)

    text = (data / "almanac" / f"almanac_agent_{stem}.md").read_text(encoding="utf-8")
    assert 'ALMANAC THESIS: "second"' in text
    assert 'ALMANAC THESIS: "first"' not in text


def test_export_discovers_stem_when_prediction_week_differs(tmp_path):
    """UI date can be W30 while artifacts live under W29 for the same run_id."""
    outputs = tmp_path / "outputs"
    data = tmp_path / "data"
    run_id = "run-mrs5oiri"
    _write_json(
        outputs / "almanac" / f"almanac_W29_{run_id}_7d.json",
        {
            "prediction_date": "2026-07-13",
            "monthly_bias": "Bullish",
            "seasonal_bias": "Bearish",
            "confidence": "Medium",
            "thesis": "Discovered stem",
            "weekly_pattern": "",
            "sector_signals": [],
        },
    )

    written = export_run_to_data(
        date(2026, 7, 20),  # W30
        run_id,
        7,
        outputs_root=outputs,
        data_root=data,
    )
    assert any(p.endswith("almanac/almanac_agent_W29.md") for p in written)
    assert "Discovered stem" in (
        data / "almanac" / "almanac_agent_W29.md"
    ).read_text(encoding="utf-8")


@pytest.fixture
def client():
    from server import create_app

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_post_export_endpoint(client, monkeypatch):
    def fake_export(prediction_date, run_id, horizon_days, **kwargs):
        return ["data/almanac/almanac_agent_W25.md"]

    monkeypatch.setattr("server.artifacts.export_run_to_data", fake_export)

    resp = client.post(
        "/artifacts/export",
        json={
            "prediction_date": "2026-06-18",
            "run_id": "run1",
            "horizon_days": 7,
        },
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ok"] is True
    assert body["written"] == ["data/almanac/almanac_agent_W25.md"]