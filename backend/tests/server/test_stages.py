import json
import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from dataclasses import asdict

from server import create_app
from agents.schemas import (
    AlmanacOutput, Bias, Confidence,
    TechnicalOutput, InstrumentTechnical,
    MacroOutput, MacroBias, CommodityData,
    EvidenceOutput,
    LLMOutput, Regime, PredictedRange,
)


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


ALMANAC_OUTPUT = AlmanacOutput(
    prediction_date=date(2026, 6, 18),
    monthly_bias=Bias.BULLISH,
    seasonal_bias=Bias.BULLISH,
    confidence=Confidence.MEDIUM,
    thesis="Test thesis",
)

TECHNICAL_OUTPUT = TechnicalOutput(
    prediction_date=date(2026, 6, 18),
    instruments={
        "SPX": InstrumentTechnical(
            last_close=5400.0, ema_8=5380.0, ema_21=5350.0,
            trend_bias=Bias.BULLISH, key_support=5300.0,
            key_resistance=5500.0, confidence=Confidence.HIGH,
        )
    },
)

MACRO_OUTPUT = MacroOutput(
    prediction_date=date(2026, 6, 18),
    fed_rate="5.25%", yield_2y=4.8, yield_10y=4.5, yield_30y=4.6,
    dxy=CommodityData(price=104.0, weekly_change=-0.3),
    wti_oil=CommodityData(price=78.0, weekly_change=1.2),
    gold=CommodityData(price=2350.0, weekly_change=0.5),
    macro_bias=MacroBias.NEUTRAL, primary_driver="Fed policy",
    confidence=Confidence.MEDIUM, invalidation="Surprise CPI print",
)

EVIDENCE_OUTPUT = EvidenceOutput(
    prediction_date=date(2026, 6, 18),
    week="W25",
    content="# W25 actuals",
)

LLM_OUT = LLMOutput(
    prediction_date=date(2026, 6, 18),
    model_name="example",
    weekly_regime=Regime.BULLISH,
    confidence=Confidence.MEDIUM,
    spx_range=PredictedRange(low=-1.0, high=2.0),
    ndx_range=PredictedRange(low=-1.5, high=2.5),
    iwm_range=PredictedRange(low=-2.0, high=1.5),
    invalidation="None",
    plain_english="Bullish week expected.",
)


def test_post_almanac_returns_output(client, tmp_path):
    with patch("server.stages.run_almanac") as mock_run, \
         patch("server.stages.artifact_path", return_value=tmp_path / "out.json"):
        mock_run.side_effect = lambda ctx, config: setattr(ctx, "almanac", ALMANAC_OUTPUT)
        resp = client.post("/stages/almanac", json={
            "prediction_date": "2026-06-18",
            "run_id": "run1",
            "horizon_days": 7,
        })
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["monthly_bias"] == "Bullish"


def test_post_almanac_missing_field(client):
    resp = client.post("/stages/almanac", json={
        "prediction_date": "2026-06-18",
        "run_id": "run1",
        # horizon_days missing
    })
    assert resp.status_code == 400
    assert "horizon_days" in json.loads(resp.data)["error"]


def test_post_almanac_bad_date(client):
    resp = client.post("/stages/almanac", json={
        "prediction_date": "not-a-date",
        "run_id": "run1",
        "horizon_days": 7,
    })
    assert resp.status_code == 400


def test_post_evidence_no_horizon(client, tmp_path):
    with patch("server.stages.run_evidence") as mock_run, \
         patch("server.stages.artifact_path", return_value=tmp_path / "out.json"):
        mock_run.side_effect = lambda ctx, config, **kw: setattr(ctx, "evidence", EVIDENCE_OUTPUT)
        resp = client.post("/stages/evidence", json={
            "prediction_date": "2026-06-18",
            "run_id": "run1",
        })
    assert resp.status_code == 200
    assert json.loads(resp.data)["week"] == "W25"


def test_post_llm_missing_agent_artifacts(client, tmp_path):
    with patch("server.stages.artifact_path", side_effect=lambda t, *a, **kw: tmp_path / f"{t}.json"):
        resp = client.post("/stages/llm", json={
            "prediction_date": "2026-06-18",
            "run_id": "run1",
            "model": "example",
            "horizon_days": 7,
        })
    assert resp.status_code == 404
    body = json.loads(resp.data)
    assert "almanac" in body["error"]


def test_post_llm_unknown_model(client):
    resp = client.post("/stages/llm", json={
        "prediction_date": "2026-06-18",
        "run_id": "run1",
        "model": "does_not_exist",
        "horizon_days": 7,
    })
    assert resp.status_code == 400
    assert "model" in json.loads(resp.data)["error"]
