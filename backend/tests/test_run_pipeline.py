import tomllib
from pathlib import Path

PIPELINE_TOML = Path(__file__).parent.parent / "pipeline.toml"


def test_pipeline_toml_exists():
    assert PIPELINE_TOML.exists(), "pipeline.toml must exist in backend/"


def test_pipeline_toml_has_required_keys():
    with open(PIPELINE_TOML, "rb") as f:
        config = tomllib.load(f)

    assert "pipeline" in config
    assert "prediction_date" in config["pipeline"]
    assert "stages" in config
    for key in ("almanac", "technical", "macro", "evidence", "delta"):
        assert key in config["stages"], f"Missing stage: {key}"
    assert "delta" in config
    assert "prediction_week" in config["delta"]
    assert "actuals_week" in config["delta"]
    assert "llm" in config
    assert "models" in config["llm"]
    assert isinstance(config["llm"]["models"], list)
    assert "artifacts" in config
    assert "save_json" in config["artifacts"]
    assert "save_md" in config["artifacts"]


def test_resolve_prediction_date_auto():
    from datetime import date
    from run_pipeline import resolve_date

    result = resolve_date("auto")
    assert result == date.today()


def test_resolve_prediction_date_iso():
    from datetime import date
    from run_pipeline import resolve_date

    result = resolve_date("2026-06-16")
    assert result == date(2026, 6, 16)
