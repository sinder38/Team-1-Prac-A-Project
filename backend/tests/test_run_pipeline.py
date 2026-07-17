from datetime import date
from pathlib import Path

PIPELINE_TOML = Path(__file__).parent.parent / "pipeline.toml"

# TODO: These tests are not nearly complete


def test_pipeline_toml_exists():
    assert PIPELINE_TOML.exists(), "pipeline.toml must exist in backend/"


def test_pipeline_toml_loads_as_valid_config():
    from agents.pipeline.config import PipelineConfig, load_config

    config = load_config(PIPELINE_TOML)
    assert isinstance(config, PipelineConfig)
    assert len(config.llm.models) > 0
    assert all(m.id for m in config.llm.models)
    assert config.delta.prediction_week == "previous"
    assert config.delta.actuals_week == "auto"


def test_resolve_prediction_date_auto():
    from run_pipeline import resolve_date

    result = resolve_date("auto")
    assert result == date.today()


def test_resolve_prediction_date_iso():
    from run_pipeline import resolve_date

    result = resolve_date("2026-06-16")
    assert result == date(2026, 6, 16)
