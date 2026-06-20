from datetime import date

import pytest

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
    assert "Test thesis" in prompt
    assert "W25 actuals" in prompt


def test_build_prompt_skips_none_agents():
    ctx = PipelineContext(prediction_date=date(2026, 6, 16))
    agent = _StubLLM()
    prompt = agent.build_prompt(date(2026, 6, 16), ctx)
    assert "No agent data available" in prompt


def test_run_evidence_populates_context(tmp_path):
    from agents.pipeline.stages import run_evidence

    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    (evidence_dir / "actuals_W25.md").write_text("# W25", encoding="utf-8")

    ctx = PipelineContext(prediction_date=date(2026, 6, 16))
    run_evidence(ctx, _no_artifacts_config(), data_root=tmp_path)

    assert ctx.evidence is not None
    assert ctx.evidence.week == "W25"
    assert ctx.evidence.content == "# W25"


def test_run_evidence_raises_on_missing_file(tmp_path):
    from agents.pipeline.stages import run_evidence

    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()

    ctx = PipelineContext(prediction_date=date(2026, 6, 16))
    with pytest.raises(FileNotFoundError, match="actuals_W25.md"):
        run_evidence(ctx, _no_artifacts_config(), data_root=tmp_path)


def test_run_almanac_populates_context():
    from agents.pipeline.stages import run_almanac

    ctx = PipelineContext(prediction_date=date(2026, 6, 16))
    run_almanac(ctx, _no_artifacts_config())
    assert ctx.almanac is not None
    assert ctx.almanac.agent_type == "almanac"
