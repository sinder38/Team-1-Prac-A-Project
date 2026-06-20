from pathlib import Path
import json
import shutil

from agents.delta.delta_engine import (
    DeltaEngine,
    parse_actuals_markdown,
    parse_prediction_markdown,
)


PREDICTION_MD = """
| Asset | Direction | Range | Confidence |
|---|---|---|---|
| S&P 500 (SPX) | **FLAT-UP** | -0.5% to +1.2% | **MEDIUM** |
| Nasdaq 100 (NDX) | **FLAT-UP** | -0.5% to +2.0% | **MEDIUM** |
| Russell 2000 (IWM) | **UP** | +0.5% to +3.0% | **MEDIUM** |
"""


ACTUALS_MD = """
| What it is | Short name | Price at Friday close | Up or down this week |
|------------|------------|----------------------|----------------------|
| S&P 500 - large U.S. companies | SPX | 7,500.58 | **Up 0.93%** |
| Nasdaq 100 - mostly tech | NDX | 30,406.19 | **Up 2.60%** |
| Russell 2000 - smaller companies | IWM | 295.59 | **Up 1.14%** |
"""


def _workspace_tmp(name: str) -> Path:
    path = Path(__file__).resolve().parents[2] / ".tmp" / name
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def test_parse_prediction_markdown_reads_tracked_assets():
    rows = parse_prediction_markdown(PREDICTION_MD)

    assert rows["SPX"].direction == "FLAT-UP"
    assert rows["SPX"].range_low == -0.5
    assert rows["SPX"].range_high == 1.2
    assert rows["IWM"].confidence == "Medium"


def test_parse_actuals_markdown_reads_actual_moves():
    rows = parse_actuals_markdown(ACTUALS_MD)

    assert rows["SPX"].actual_move == 0.93
    assert rows["NDX"].actual_direction == "UP"
    assert rows["IWM"].actual_move == 1.14


def test_delta_engine_scores_direction_and_range():
    tmp_path = _workspace_tmp("delta-score")
    prediction_path = tmp_path / "prediction.md"
    actuals_path = tmp_path / "actuals.md"
    prediction_path.write_text(PREDICTION_MD, encoding="utf-8")
    actuals_path.write_text(ACTUALS_MD, encoding="utf-8")

    report = DeltaEngine(repo_root=tmp_path).run(
        prediction_path=prediction_path,
        actuals_path=actuals_path,
        prediction_week="vW24",
        actuals_week="W24",
    )

    assert report.direction_correct_count == 3
    assert report.range_hit_count == 2
    assert report.rows[0].asset == "SPX"
    assert report.rows[0].range_hit is True
    assert report.rows[1].error_percent == 0.60
    assert report.rows[2].range_hit is True
    assert "NDX moved outside the range" in report.prescription
    assert report.weight_adjustments[2].agent == "technical"
    assert report.weight_adjustments[2].suggested_weight == 0.30


def test_delta_engine_writes_markdown_and_json():
    tmp_path = _workspace_tmp("delta-write")
    prediction_path = tmp_path / "prediction.md"
    actuals_path = tmp_path / "actuals.md"
    output_path = tmp_path / "delta_W24.md"
    json_path = tmp_path / "delta_W24.json"
    prediction_path.write_text(PREDICTION_MD, encoding="utf-8")
    actuals_path.write_text(ACTUALS_MD, encoding="utf-8")

    engine = DeltaEngine(repo_root=tmp_path)
    report = engine.run(
        prediction_path=prediction_path,
        actuals_path=actuals_path,
        prediction_week="vW24",
        actuals_week="W24",
    )
    written_path = engine.write_markdown(report, output_path)
    written_json_path = engine.write_json(report, json_path)

    assert written_path == output_path
    assert written_json_path == json_path
    content = Path(output_path).read_text(encoding="utf-8")
    assert "Direction accuracy: 3 / 3" in content
    assert "Range accuracy: 2 / 3" in content
    assert "| NDX | FLAT-UP | -0.5% to +2.0% | Medium | +2.60% | UP | Y | N | 0.60% |" in content
    assert "Weight adjustment draft" in content
    assert "technical | 0.25 | 0.30" in content

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["prediction_week"] == "vW24"
    assert data["actuals_week"] == "W24"
    assert data["weight_adjustments"][2]["agent"] == "technical"
