import json
from datetime import date
from unittest.mock import patch

from agents.schemas import (
    AlmanacOutput, Bias, Confidence,
    TechnicalOutput, InstrumentTechnical,
    MacroOutput, MacroBias, CommodityData,
    EvidenceOutput,
    LLMOutput, Regime, PredictedRange,
)


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


def test_post_almanac_returns_output(client):
    with patch("server.stages.run_almanac") as mock_run:
        mock_run.side_effect = lambda ctx, config: setattr(ctx, "almanac", ALMANAC_OUTPUT)
        resp = client.post("/stages/almanac", json={
            "prediction_date": "2026-06-18",
            "run_id": "run1",
            "horizon_days": 7,
        })
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["monthly_bias"] == "Bullish"
    assert data["horizon_days"] == 7

    # Round-trip: the output was persisted and is readable via /artifacts.
    got = client.get(
        "/artifacts/almanac?run_id=run1&horizon_days=7&prediction_date=2026-06-18"
    )
    assert got.status_code == 200
    assert json.loads(got.data)["monthly_bias"] == "Bullish"


def test_post_technical_round_trip(client):
    with patch("server.stages.run_technical") as mock_run:
        mock_run.side_effect = lambda ctx, config: setattr(ctx, "technical", TECHNICAL_OUTPUT)
        resp = client.post("/stages/technical", json={
            "prediction_date": "2026-06-18",
            "run_id": "run1",
            "horizon_days": 7,
        })
    assert resp.status_code == 200

    got = client.get(
        "/artifacts/technical?run_id=run1&horizon_days=7&prediction_date=2026-06-18"
    )
    assert got.status_code == 200
    assert json.loads(got.data)["instruments"]["SPX"]["last_close"] == 5400.0


def test_post_almanac_conflicting_run_id(client):
    """Reusing a run_id with a different prediction_date is a 409."""
    with patch("server.stages.run_almanac") as mock_run:
        mock_run.side_effect = lambda ctx, config: setattr(ctx, "almanac", ALMANAC_OUTPUT)
        first = client.post("/stages/almanac", json={
            "prediction_date": "2026-06-18",
            "run_id": "run1",
            "horizon_days": 7,
        })
        assert first.status_code == 200
        conflict = client.post("/stages/almanac", json={
            "prediction_date": "2026-06-25",  # same run_id, different date
            "run_id": "run1",
            "horizon_days": 7,
        })
    assert conflict.status_code == 409


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


def test_post_evidence_no_horizon(client):
    with patch("server.stages.run_evidence") as mock_run:
        mock_run.side_effect = lambda ctx, config, **kw: setattr(ctx, "evidence", EVIDENCE_OUTPUT)
        resp = client.post("/stages/evidence", json={
            "prediction_date": "2026-06-18",
            "run_id": "run1",
        })
    assert resp.status_code == 200
    body = json.loads(resp.data)
    assert body["week"] == "W25"
    assert "generated_at" in body


def test_post_llm_missing_agent_artifacts(client):
    from agents.pipeline.config import LLMModelEntry

    # No agent artifacts seeded for this run_id, so the LLM stage should 404.
    with patch.dict(
        "server.stages._MODEL_REGISTRY",
        {"example": LLMModelEntry(id="example/example:free")},
    ):
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


def test_list_models(client):
    resp = client.get("/stages/models")
    assert resp.status_code == 200
    models = json.loads(resp.data)["models"]
    assert models
    assert all("key" in m and "name" in m and "provider" in m for m in models)
    keys = {m["key"] for m in models}
    # server.toml exposes both Local (ollama) and Real API (openrouter).
    # Slugs are unified with the CI auto-derivation (2026-07 model rotation).
    assert "llama3.2-3b" in keys
    assert "nemotron-3-super-120b-a12b" in keys
    # Rotation guard: new models present, delisted ones gone.
    assert {"gpt-oss-20b", "laguna-xs-2.1"} <= keys
    assert not {"gpt-oss-120b", "laguna-m.1", "gptoss", "laguna"} & keys
    by_key = {m["key"]: m["provider"] for m in models}
    assert by_key["llama3.2-3b"] == "ollama"
    # Also pins the provider default: openrouter entries omit `provider`
    # in server.toml and rely on LLMModelEntry's default.
    assert by_key["nemotron-3-super-120b-a12b"] == "openrouter"
    assert by_key["gpt-oss-20b"] == "openrouter"


# --- POST /stages/human ------------------------------------------------------

_HUMAN_FORM = {
    "scores": {"macro": 0, "technical": 1, "almanac": -1, "aiAgreement": 1, "wildCard": 1},
    "reasoning": {
        "macro": "Balanced macro.",
        "technical": "Bullish across indices.",
        "almanac": "June midterm weakness.",
        "aiAgreement": "4 of 4 models agree.",
        "wildCard": "Tech concentration risk.",
    },
    "humanCall": "Neutral-Bullish",
    "confidence": "Medium",
    "overrideParagraph": "We agree cautiously.",
    "wildCardInsight": "Leadership concentrated in tech.",
    "invalidation": "Break below key support.",
    "evidence": {"almanac": True, "macro": True, "technical": True, "llm": True},
}


def test_post_human_persists_and_exports(client):
    resp = client.post("/stages/human", json={
        "prediction_date": "2026-06-21",
        "run_id": "run-h",
        "horizon_days": 7,
        "week": "W25",
        "form": _HUMAN_FORM,
        "consensus": "Uncertain / Neutral",
        "aiSaid": {"macro": "Binary-risk"},
        "total": 2,
    })
    assert resp.status_code == 200
    body = json.loads(resp.data)
    assert body["ok"] is True
    assert body["week"] == "W25"
    assert body["total"] == 2

    # The stored report is now exportable as human_score_W25.md.
    export = client.post("/export", json={"run_id": "run-h", "write": False})
    assert export.status_code == 200
    arts = json.loads(export.data)["artifacts"]
    hs = next(a for a in arts if a["agent_type"] == "human_score")
    assert hs["filename"] == "human_score_W25.md"
    md = hs["markdown"]
    assert "# Human Score Analyst Output — Week 25" in md
    assert "## Five-Dimension Judgement" in md
    assert "**+2**" in md
    assert "Neutral-Bullish" in md


def test_post_human_computes_total_when_missing(client):
    resp = client.post("/stages/human", json={
        "prediction_date": "2026-06-21",
        "run_id": "run-h2",
        "form": _HUMAN_FORM,
    })
    assert resp.status_code == 200
    # 0 + 1 - 1 + 1 + 1 = 2
    assert json.loads(resp.data)["total"] == 2


def test_post_human_requires_form(client):
    resp = client.post("/stages/human", json={
        "prediction_date": "2026-06-21",
        "run_id": "run-h3",
    })
    assert resp.status_code == 400
