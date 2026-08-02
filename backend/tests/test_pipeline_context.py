from datetime import date
from core.schemas import EvidenceOutput
from pipeline.context import PipelineContext


def test_evidence_output_fields():
    out = EvidenceOutput(
        prediction_date=date(2026, 6, 16),
        week="W25",
        content="# Week 25\nSPX up 1%",
    )
    assert out.week == "W25"
    assert out.content == "# Week 25\nSPX up 1%"
    assert out.agent_type == "evidence"
    assert out.prediction_date == date(2026, 6, 16)


def test_pipeline_context_defaults():
    ctx = PipelineContext(prediction_date=date(2026, 6, 16))
    assert ctx.almanac is None
    assert ctx.technical is None
    assert ctx.macro is None
    assert ctx.evidence is None
    assert ctx.llm_outputs == []


def test_pipeline_context_stores_outputs():
    ctx = PipelineContext(prediction_date=date(2026, 6, 16))
    ev = EvidenceOutput(
        prediction_date=date(2026, 6, 16),
        week="W25",
        content="# Week 25",
    )
    ctx.evidence = ev
    assert ctx.evidence.week == "W25"


def test_pipeline_context_horizon_default():
    ctx = PipelineContext(prediction_date=date(2026, 6, 16))
    assert ctx.horizon_days == 7


def test_pipeline_context_horizon_custom():
    ctx = PipelineContext(prediction_date=date(2026, 6, 16), horizon_days=14)
    assert ctx.horizon_days == 14
