from datetime import date

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


import pytest
from pathlib import Path
from agents.pipeline.stages import run_evidence, run_almanac, LLM_REGISTRY


def test_run_evidence_populates_context(tmp_path):
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    (evidence_dir / "actuals_W25.md").write_text("# W25", encoding="utf-8")

    ctx = PipelineContext(prediction_date=date(2026, 6, 16))
    config = {"artifacts": {"save_json": False, "save_md": False}}
    run_evidence(ctx, config, data_root=tmp_path)

    assert ctx.evidence is not None
    assert ctx.evidence.week == "W25"
    assert ctx.evidence.content == "# W25"


def test_run_evidence_raises_on_missing_file(tmp_path):
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()

    ctx = PipelineContext(prediction_date=date(2026, 6, 16))
    config = {"artifacts": {"save_json": False, "save_md": False}}
    with pytest.raises(FileNotFoundError, match="actuals_W25.md"):
        run_evidence(ctx, config, data_root=tmp_path)


def test_run_almanac_populates_context():
    ctx = PipelineContext(prediction_date=date(2026, 6, 16))
    config = {"artifacts": {"save_json": False, "save_md": False}}
    run_almanac(ctx, config)
    assert ctx.almanac is not None
    assert ctx.almanac.agent_type == "almanac"


def test_llm_registry_contains_example():
    assert "example" in LLM_REGISTRY
