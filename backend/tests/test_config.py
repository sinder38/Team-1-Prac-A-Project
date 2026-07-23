import pytest
from pathlib import Path
from pydantic import ValidationError

PIPELINE_TOML = Path(__file__).parent.parent / "pipeline.toml"


def test_llm_model_entry_slug():
    from pipeline.config import LLMModelEntry
    entry = LLMModelEntry(id="nvidia/nemotron-3-super-120b-a12b:free")
    assert entry.slug == "nemotron-3-super-120b-a12b"


def test_llm_model_entry_label():
    from pipeline.config import LLMModelEntry
    entry = LLMModelEntry(id="nvidia/nemotron-3-super-120b-a12b:free")
    assert entry.label == "Nemotron 3 Super 120B A12B"


def test_llm_model_entry_no_variant():
    from pipeline.config import LLMModelEntry
    entry = LLMModelEntry(id="openai/gpt-4o")
    assert entry.slug == "gpt-4o"
    assert entry.label == "Gpt 4O"


def test_load_config_valid(tmp_path):
    from pipeline.config import load_config, PipelineConfig
    toml = tmp_path / "pipeline.toml"
    toml.write_text("""
[pipeline]
prediction_date = "2026-06-08"

[stages]
almanac = true
technical = true
macro = true
evidence = true

[llm]
models = [
    {id = "nvidia/nemotron-3-super-120b-a12b:free"},
]
max_retries = 3

[artifacts]
save_json = false
save_md = true
""")
    config = load_config(toml)
    assert isinstance(config, PipelineConfig)
    assert config.pipeline.prediction_date == "2026-06-08"
    assert config.stages.almanac is True
    assert len(config.llm.models) == 1
    assert config.llm.models[0].slug == "nemotron-3-super-120b-a12b"
    assert config.artifacts.save_md is True


def test_load_config_missing_pipeline_section(tmp_path):
    from pipeline.config import load_config
    toml = tmp_path / "bad.toml"
    toml.write_text("""
[stages]
almanac = true
[llm]
models = [{id = "openai/gpt-oss-20b:free"}]
""")
    with pytest.raises(ValidationError):
        load_config(toml)


def test_load_config_missing_llm_section(tmp_path):
    from pipeline.config import load_config
    toml = tmp_path / "bad.toml"
    toml.write_text("""
[pipeline]
prediction_date = "2026-06-08"
[stages]
almanac = true
""")
    with pytest.raises(ValidationError):
        load_config(toml)


def test_load_config_bad_models_old_shape(tmp_path):
    from pipeline.config import load_config
    toml = tmp_path / "bad.toml"
    toml.write_text("""
[pipeline]
prediction_date = "2026-06-08"
[stages]
almanac = true
[llm]
models = ["nemotron", "gptoss"]
""")
    with pytest.raises(ValidationError):
        load_config(toml)


def test_load_config_artifacts_defaults(tmp_path):
    from pipeline.config import load_config
    toml = tmp_path / "pipeline.toml"
    toml.write_text("""
[pipeline]
prediction_date = "auto"
[stages]
almanac = false
technical = false
macro = false
evidence = false
[llm]
models = [{id = "openai/gpt-oss-20b:free"}]
max_retries = 3
""")
    config = load_config(toml)
    assert config.artifacts.save_json is True
    assert config.artifacts.save_md is True
