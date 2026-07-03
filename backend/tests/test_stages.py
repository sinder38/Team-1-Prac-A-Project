from datetime import date
from pathlib import Path

import pandas as pd

from agents.pipeline.context import PipelineContext
from agents.llm.base_llm import BaseLLMAgent
from agents.schemas import (
    AlmanacOutput, Bias, Confidence,
    EvidenceOutput,
)


class _StubLLM(BaseLLMAgent):
    model_name = "stub"
    def query(self, prompt: str) -> str:
        return prompt  # echo back so we can inspect


DELTA_PREDICTION_MD = """
| Asset | Direction | Range | Confidence |
|---|---|---|---|
| S&P 500 (SPX) | **FLAT-UP** | -0.5% to +1.2% | **MEDIUM** |
| Nasdaq 100 (NDX) | **FLAT-UP** | -0.5% to +2.0% | **MEDIUM** |
| Russell 2000 (IWM) | **UP** | +0.5% to +3.0% | **MEDIUM** |
"""


DELTA_ACTUALS_MD = """
| What it is | Short name | Price at Friday close | Up or down this week |
|------------|------------|----------------------|----------------------|
| S&P 500 - large U.S. companies | SPX | 7,500.58 | **Up 0.93%** |
| Nasdaq 100 - mostly tech | NDX | 30,406.19 | **Up 2.60%** |
| Russell 2000 - smaller companies | IWM | 295.59 | **Up 1.14%** |
"""


def _write_delta_inputs(repo_root: Path) -> None:
    prediction_dir = repo_root / "data" / "final prediction"
    actuals_dir = repo_root / "data" / "evidence"
    prediction_dir.mkdir(parents=True)
    actuals_dir.mkdir(parents=True)
    (prediction_dir / "prediction_2026-W24_Team1.md").write_text(
        DELTA_PREDICTION_MD,
        encoding="utf-8",
    )
    (actuals_dir / "actuals_W25.md").write_text(
        DELTA_ACTUALS_MD,
        encoding="utf-8",
    )


def test_build_prompt_uses_context():
    ctx = PipelineContext(prediction_date=date(2026, 6, 16))
    ctx.almanac = AlmanacOutput(
        prediction_date=date(2026, 6, 16),
        monthly_bias=Bias.BULLISH,
        seasonal_bias=Bias.BULLISH,
        confidence=Confidence.MEDIUM,
        thesis="Test thesis",
    )
    ctx.evidence = EvidenceOutput(
        prediction_date=date(2026, 6, 16),
        week="W25",
        content="# W25 actuals",
    )

    agent = _StubLLM()
    prompt = agent.build_prompt(date(2026, 6, 16), ctx)

    assert "ALMANAC" in prompt
    assert "EVIDENCE" in prompt
    assert "Test thesis" in prompt
    assert "W25 actuals" in prompt


def test_build_prompt_skips_none_agents():
    ctx = PipelineContext(prediction_date=date(2026, 6, 16))
    # No agents set — context is empty
    agent = _StubLLM()
    prompt = agent.build_prompt(date(2026, 6, 16), ctx)
    assert "No agent data available" in prompt


from agents.pipeline.stages import run_delta, run_evidence, run_almanac, LLM_REGISTRY


class _FakeEvidenceMarketDataProvider:
    def history(self, ticker: str, start: date, end: date) -> pd.Series:
        dates = pd.to_datetime(
            [
                "2026-06-12",
                "2026-06-15",
                "2026-06-16",
                "2026-06-17",
                "2026-06-18",
                "2026-06-19",
            ]
        )
        current = 101.0
        return pd.Series([100.0, 100.2, 100.4, 100.6, 100.8, current], index=dates)


class _FakeEvidenceYieldDataProvider:
    def history(self, series_id: str, start: date, end: date) -> pd.Series:
        dates = pd.to_datetime(
            [
                "2026-06-12",
                "2026-06-15",
                "2026-06-16",
                "2026-06-17",
                "2026-06-18",
                "2026-06-19",
            ]
        )
        return pd.Series([4.50, 4.48, 4.47, 4.46, 4.45, 4.44], index=dates)


def test_run_evidence_populates_context(tmp_path):
    ctx = PipelineContext(prediction_date=date(2026, 6, 16))
    config = {"artifacts": {"save_json": False, "save_md": False}}
    run_evidence(
        ctx,
        config,
        data_root=tmp_path,
        market_data_provider=_FakeEvidenceMarketDataProvider(),
        yield_data_provider=_FakeEvidenceYieldDataProvider(),
    )

    assert ctx.evidence is not None
    assert ctx.evidence.week == "W25"
    assert ctx.evidence.content.startswith("# Week 05 Market Report (2026)")


def test_run_evidence_does_not_require_manual_actuals_file(tmp_path):
    ctx = PipelineContext(prediction_date=date(2026, 6, 16))
    config = {"artifacts": {"save_json": False, "save_md": False}}
    run_evidence(
        ctx,
        config,
        data_root=tmp_path,
        market_data_provider=_FakeEvidenceMarketDataProvider(),
        yield_data_provider=_FakeEvidenceYieldDataProvider(),
    )
    assert ctx.evidence is not None
    assert "10-year Treasury yield from FRED series DGS10" in ctx.evidence.content


def test_run_almanac_populates_context():
    ctx = PipelineContext(prediction_date=date(2026, 6, 16))
    config = {"artifacts": {"save_json": False, "save_md": False}}
    run_almanac(ctx, config)
    assert ctx.almanac is not None
    assert ctx.almanac.agent_type == "almanac"


def test_run_delta_populates_context_and_writes_outputs(tmp_path):
    _write_delta_inputs(tmp_path)

    ctx = PipelineContext(prediction_date=date(2026, 6, 16))
    config = {
        "delta": {"prediction_week": "W24", "actuals_week": "W25"},
        "artifacts": {"save_json": True, "save_md": True},
    }
    run_delta(ctx, config, repo_root=tmp_path)

    assert ctx.delta is not None
    assert ctx.delta.direction_correct_count == 3
    assert (tmp_path / "data" / "qa" / "delta_W24.md").exists()
    assert (tmp_path / "data" / "outputs" / "delta" / "delta_W24.json").exists()


def test_delta_context_can_feed_llm_prompt(tmp_path):
    _write_delta_inputs(tmp_path)

    ctx = PipelineContext(prediction_date=date(2026, 6, 16))
    config = {
        "delta": {"prediction_week": "W24", "actuals_week": "W25"},
        "artifacts": {"save_json": False, "save_md": False},
    }
    run_delta(ctx, config, repo_root=tmp_path)

    prompt = _StubLLM().build_prompt(date(2026, 6, 16), ctx)

    assert "DELTA AGENT" in prompt
    assert "weight_adjustments" in prompt
    assert "prescription" in prompt


def test_llm_registry_contains_example():
    assert "example" in LLM_REGISTRY
