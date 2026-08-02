import json
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from pipeline.config import (
    ArtifactsConfig,
    DeltaConfig,
    LLMConfig,
    PipelineConfig,
    PipelineSection,
    StagesConfig,
)
from pipeline.context import PipelineContext
from pipeline.stages import run_delta

PREDICTION = """
| Asset | Direction | Range | Confidence |
| --- | --- | --- | --- |
| S&P 500 (SPX) | UP | -0.5% to +1.2% | MEDIUM |
| Nasdaq 100 (NDX) | UP | -0.5% to +2.0% | MEDIUM |
| Russell 2000 (IWM) | UP | +0.5% to +3.0% | MEDIUM |
"""

ACTUALS = """
| Asset | Up or down this week |
| --- | --- |
| S&P 500 (SPX) | Up 0.9% |
| Nasdaq 100 (NDX) | Up 2.6% |
| Russell 2000 (IWM) | Up 1.1% |
"""


def _config() -> PipelineConfig:
    return PipelineConfig(
        pipeline=PipelineSection(prediction_date="2026-06-15"),
        stages=StagesConfig(delta=True),
        delta=DeltaConfig(prediction_week="previous", actuals_week="auto"),
        llm=LLMConfig(models=[], max_retries=1),
        artifacts=ArtifactsConfig(save_json=True, save_md=True),
    )


def _write_input_pair(repo_root):
    prediction_dir = repo_root / "data" / "final prediction"
    actuals_dir = repo_root / "data" / "evidence"
    prediction_dir.mkdir(parents=True)
    actuals_dir.mkdir(parents=True)
    (prediction_dir / "prediction_2026-W24_Team1.md").write_text(
        PREDICTION,
        encoding="utf-8",
    )
    (actuals_dir / "actuals_W25.md").write_text(
        ACTUALS,
        encoding="utf-8",
    )


def test_run_delta_populates_context_and_writes_artifacts(tmp_path):
    _write_input_pair(tmp_path)
    context = PipelineContext(prediction_date=date(2026, 6, 15))

    run_delta(context, _config(), repo_root=tmp_path)

    assert context.delta is not None
    assert context.delta.prediction_week == "vW24"
    assert (tmp_path / "data" / "qa" / "delta_W25.md").exists()
    assert (tmp_path / "data" / "outputs" / "delta" / "delta_W25.json").exists()


def test_run_delta_checks_all_outputs_before_writing(tmp_path):
    _write_input_pair(tmp_path)
    markdown_path = tmp_path / "data" / "qa" / "delta_W25.md"
    json_path = tmp_path / "data" / "outputs" / "delta" / "delta_W25.json"
    markdown_path.parent.mkdir(parents=True)
    json_path.parent.mkdir(parents=True)
    original_markdown = (
        "# Existing report\n\n- Locked prediction: vW24\n- Completed actuals: W25\n"
    )
    markdown_path.write_text(original_markdown, encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "prediction_week": "vW25",
                "actuals_week": "W26",
            }
        ),
        encoding="utf-8",
    )
    context = PipelineContext(prediction_date=date(2026, 6, 15))

    with pytest.raises(FileExistsError, match="contains W25/W26"):
        run_delta(context, _config(), repo_root=tmp_path)

    assert markdown_path.read_text(encoding="utf-8") == original_markdown


def test_run_delta_rejects_actuals_before_friday_close(tmp_path):
    context = PipelineContext(prediction_date=date(2026, 7, 13))
    before_close = datetime(
        2026,
        7,
        17,
        15,
        30,
        tzinfo=ZoneInfo("America/New_York"),
    )

    with pytest.raises(ValueError, match="not complete"):
        run_delta(context, _config(), repo_root=tmp_path, now=before_close)
