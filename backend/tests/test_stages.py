from datetime import date

import pandas as pd

from agents.llm.base_llm import BaseLLMAgent
from agents.pipeline.config import (
    ArtifactsConfig,
    LLMConfig,
    LLMModelEntry,
    PipelineConfig,
    PipelineSection,
    StagesConfig,
)
from agents.pipeline.context import PipelineContext
from agents.schemas import AlmanacOutput, Bias, Confidence, EvidenceOutput


def _no_artifacts_config() -> PipelineConfig:
    return PipelineConfig(
        pipeline=PipelineSection(prediction_date="2026-06-16"),
        stages=StagesConfig(),
        llm=LLMConfig(models=[LLMModelEntry(id="openai/gpt-oss-120b:free")]),
        artifacts=ArtifactsConfig(save_json=False, save_md=False),
    )


class _StubLLM(BaseLLMAgent):
    model_name = "stub"

    def query(self, prompt: str) -> str:
        return prompt


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
    assert "EVIDENCE" in prompt
    assert "Test thesis" in prompt
    assert "W25 actuals" in prompt


def test_build_prompt_skips_none_agents():
    ctx = PipelineContext(prediction_date=date(2026, 6, 16))
    agent = _StubLLM()
    prompt = agent.build_prompt(date(2026, 6, 16), ctx)
    assert "No agent data available" in prompt


from agents.pipeline.stages import run_evidence, run_almanac


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
    run_evidence(
        ctx,
        _no_artifacts_config(),
        data_root=tmp_path,
        market_data_provider=_FakeEvidenceMarketDataProvider(),
        yield_data_provider=_FakeEvidenceYieldDataProvider(),
    )

    assert ctx.evidence is not None
    assert ctx.evidence.week == "W25"
    assert ctx.evidence.content.startswith("# Week 05 Market Report (2026)")


def test_run_evidence_does_not_require_manual_actuals_file(tmp_path):
    ctx = PipelineContext(prediction_date=date(2026, 6, 16))
    run_evidence(
        ctx,
        _no_artifacts_config(),
        data_root=tmp_path,
        market_data_provider=_FakeEvidenceMarketDataProvider(),
        yield_data_provider=_FakeEvidenceYieldDataProvider(),
    )
    assert ctx.evidence is not None
    assert "10-year Treasury yield from FRED series DGS10" in ctx.evidence.content


def test_run_evidence_creates_chart_png_files(tmp_path):
    ctx = PipelineContext(prediction_date=date(2026, 6, 16))
    run_evidence(
        ctx,
        _no_artifacts_config(),
        data_root=tmp_path,
        market_data_provider=_FakeEvidenceMarketDataProvider(),
        yield_data_provider=_FakeEvidenceYieldDataProvider(),
    )
    evidence_dir = tmp_path / "evidence"
    performance_path = evidence_dir / "finviz_1W_2026_W25.png"
    sector_path = evidence_dir / "finviz_sectors_5D_2026_W25.png"
    assert performance_path.exists()
    assert sector_path.exists()
    assert performance_path.read_bytes().startswith(b"\x89PNG")
    assert sector_path.read_bytes().startswith(b"\x89PNG")


def test_run_almanac_populates_context():
    from agents.pipeline.stages import run_almanac

    ctx = PipelineContext(prediction_date=date(2026, 6, 16))
    run_almanac(ctx, _no_artifacts_config())
    assert ctx.almanac is not None
    assert ctx.almanac.agent_type == "almanac"
