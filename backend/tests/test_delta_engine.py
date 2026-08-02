import json
from pathlib import Path

import pytest

from agents.delta import DeltaAgent
from agents.delta.models import SECTOR_ASSETS, DeltaReport
from agents.delta.parsing import (
    parse_actuals_markdown,
    parse_prediction_json,
    parse_prediction_markdown,
)
from agents.delta.report import render_delta_markdown
from run_delta_engine import REPO_ROOT, display_path

CORE_PREDICTION = """
| Asset | Direction | Range | Confidence |
| --- | --- | --- | --- |
| S&P 500 (SPX) | FLAT-UP | -0.5% to +1.2% | MEDIUM |
| Nasdaq 100 (NDX) | FLAT-UP | -0.5% to +2.0% | MEDIUM |
| Russell 2000 (IWM) | UP | +0.5% to +3.0% | MEDIUM |
"""

SECTOR_PREDICTION = """
| Sector | Direction | Confidence |
| --- | --- | --- |
| Technology (XLK) | UP | MEDIUM |
| Health Care (XLV) | DOWN | LOW |
| Financials (XLF) | UP | MEDIUM |
| Consumer Discretionary (XLY) | UP | LOW |
| Communication Services (XLC) | UP | MEDIUM |
| Industrials (XLI) | DOWN | LOW |
| Consumer Staples (XLP) | DOWN | MEDIUM |
| Energy (XLE) | UP | MEDIUM |
| Materials (XLB) | DOWN | LOW |
| Real Estate (XLRE) | DOWN | LOW |
| Utilities (XLU) | DOWN | MEDIUM |
"""

ACTUALS = """
| What it is | Short name | Price | Up or down this week |
| --- | --- | --- | --- |
| S&P 500 | SPX | 7,500.58 | Up 0.93% |
| Nasdaq 100 | NDX | 30,406.19 | Up 2.60% |
| Russell 2000 | IWM | 295.59 | Up 1.14% |

| Rank | Industry group | Up or down this week |
| --- | --- | --- |
| 1 | Energy | Up 2.87% |
| 2 | Technology | Up 2.83% |
| 3 | Communication | Up 1.83% |
| 4 | Consumer discretionary | Up 0.28% |
| 5 | Financials | Up 0.12% |
| 6 | Industrials | Down 0.80% |
| 7 | Utilities | Down 0.89% |
| 8 | Real estate | Down 0.96% |
| 9 | Consumer staples | Down 1.10% |
| 10 | Health care | Down 1.86% |
| 11 | Materials | Down 1.93% |
"""


def test_display_path_accepts_repository_and_external_paths(tmp_path):
    repository_path = REPO_ROOT / "data" / "qa" / "delta_W24.md"
    external_path = tmp_path / "delta_W24.md"

    assert display_path(repository_path) == Path("data/qa/delta_W24.md")
    assert display_path(external_path) == external_path


def _write_pair(
    repo_root,
    prediction_week: str,
    actuals_week: str,
    prediction: str = CORE_PREDICTION,
    actuals: str = ACTUALS,
    underscore: bool = False,
):
    prediction_dir = repo_root / "data" / "final prediction"
    actuals_dir = repo_root / "data" / "evidence"
    prediction_dir.mkdir(parents=True, exist_ok=True)
    actuals_dir.mkdir(parents=True, exist_ok=True)
    separator = "_" if underscore else "-"
    prediction_path = (
        prediction_dir / f"prediction_2026{separator}{prediction_week}_Team1.md"
    )
    actuals_path = actuals_dir / f"actuals_{actuals_week}.md"
    prediction_path.write_text(prediction, encoding="utf-8")
    actuals_path.write_text(actuals, encoding="utf-8")
    return prediction_path, actuals_path


def test_parsers_read_core_indexes_and_all_sectors():
    predictions = parse_prediction_markdown(CORE_PREDICTION + SECTOR_PREDICTION)
    actuals = parse_actuals_markdown(ACTUALS)

    assert predictions["SPX"].range_low == -0.5
    assert predictions["XLK"].direction == "UP"
    assert predictions["XLK"].range_low is None
    assert actuals["NDX"].actual_move == 2.60
    assert actuals["XLB"].actual_move == -1.93
    assert all(sector in actuals for sector in SECTOR_ASSETS)


def test_json_parser_combines_index_and_sector_lists():
    rows = parse_prediction_json(
        {
            "indices": [
                {
                    "asset": "SPX",
                    "direction": "UP",
                    "range": {"low": -0.5, "high": 1.5},
                },
                {"asset": "NDX", "direction": "UP"},
                {"asset": "IWM", "direction": "FLAT"},
            ],
            "sectors": [
                {"ticker": "XLK", "direction": "UP"},
                {"ticker": "XLE", "direction": "DOWN"},
            ],
        }
    )

    assert set(rows) == {"SPX", "NDX", "IWM", "XLK", "XLE"}
    assert rows["SPX"].range_low == -0.5
    assert rows["SPX"].range_high == 1.5


def test_engine_scores_fourteen_assets_without_inventing_sector_ranges(
    tmp_path,
):
    prediction_path, actuals_path = _write_pair(
        tmp_path,
        "W28",
        "W29",
        prediction=CORE_PREDICTION + SECTOR_PREDICTION,
    )

    report = DeltaAgent(repo_root=tmp_path).run(
        prediction_week="W28",
        actuals_week="W29",
        prediction_path=prediction_path,
        actuals_path=actuals_path,
    )

    assert len(report.rows) == 14
    assert report.direction_correct_count == 14
    assert report.ranged_asset_count == 3
    assert report.range_hit_count == 2
    assert report.missing_prediction_assets == []
    xlk = next(row for row in report.rows if row.asset == "XLK")
    assert xlk.range_hit is None
    assert xlk.error_percent is None


def test_engine_reports_missing_sector_predictions_for_old_format(tmp_path):
    prediction_path, actuals_path = _write_pair(
        tmp_path,
        "W28",
        "W29",
    )

    report = DeltaAgent(repo_root=tmp_path).run(
        prediction_week="W28",
        actuals_week="W29",
        prediction_path=prediction_path,
        actuals_path=actuals_path,
    )
    markdown = render_delta_markdown(report)

    assert len(report.rows) == 3
    assert report.missing_prediction_assets == list(SECTOR_ASSETS)
    assert "Sector coverage: 0 / 11" in markdown
    assert "Missing prediction rows" in markdown


@pytest.mark.parametrize("actuals_week", ["W28", "W30"])
def test_engine_rejects_current_or_future_week_actuals(
    tmp_path,
    actuals_week,
):
    prediction_path, actuals_path = _write_pair(
        tmp_path,
        "W28",
        actuals_week,
    )

    with pytest.raises(ValueError, match="only be scored against W29"):
        DeltaAgent(repo_root=tmp_path).run(
            prediction_week="W28",
            actuals_week=actuals_week,
            prediction_path=prediction_path,
            actuals_path=actuals_path,
        )


def test_agent_builds_cumulative_history_from_completed_pairs(tmp_path):
    _write_pair(tmp_path, "W22", "W23")
    _write_pair(tmp_path, "W23", "W24")
    _write_pair(tmp_path, "W25", "W26")
    (tmp_path / "data" / "evidence" / "actuals_W26.md").unlink()
    _write_pair(tmp_path, "W28", "W29", underscore=True)

    report = DeltaAgent(repo_root=tmp_path).run("W28", "W29")

    assert [item.prediction_week for item in report.history] == [
        "W22",
        "W23",
        "W28",
    ]
    assert any("W25" in note and "missing" in note for note in report.history_notes)
    assert 0.0 <= report.cumulative_direction_accuracy <= 100.0
    assert sum(
        item.suggested_weight for item in report.weight_adjustments
    ) == pytest.approx(1.0)


def test_agent_writes_markdown_and_structured_json(tmp_path):
    _write_pair(tmp_path, "W28", "W29", underscore=True)
    agent = DeltaAgent(repo_root=tmp_path)
    report = agent.run("vW28", "W29")

    markdown_path, json_path = agent.write_outputs(report)
    data = json.loads(json_path.read_text(encoding="utf-8"))

    assert markdown_path.name == "delta_W29.md"
    assert data["schema_version"] == 2
    assert data["prediction_week"] == "vW28"
    assert data["actuals_week"] == "W29"
    assert data["history"][0]["prediction_week"] == "W28"
    assert "Prescription for next sprint" in markdown_path.read_text(encoding="utf-8")


def test_report_can_be_rebuilt_from_json(tmp_path):
    _write_pair(tmp_path, "W28", "W29", underscore=True)
    agent = DeltaAgent(repo_root=tmp_path)
    report = agent.run("W28", "W29")
    _, json_path = agent.write_outputs(report)

    restored = DeltaReport.from_dict(json.loads(json_path.read_text(encoding="utf-8")))

    assert restored == report


def _weights_json(prediction_week: str, actuals_week: str, marker: float) -> str:
    """A minimal schema-2 payload whose weights identify their source file."""
    from agents.delta.models import AGENT_ORDER

    remainder = round((1.0 - marker) / (len(AGENT_ORDER) - 1), 6)
    adjustments = [
        {"agent": agent, "suggested_weight": marker if index == 0 else remainder}
        for index, agent in enumerate(AGENT_ORDER)
    ]
    return json.dumps(
        {
            "schema_version": 2,
            "prediction_week": prediction_week,
            "actuals_week": actuals_week,
            "weight_adjustments": adjustments,
        }
    )


def test_write_outputs_files_artifacts_under_actuals_week(tmp_path):
    """The Delta artifact carries the same W-label as the rest of the run."""
    _write_pair(tmp_path, "W28", "W29", underscore=True)
    agent = DeltaAgent(repo_root=tmp_path)
    report = agent.run("vW28", "W29")

    markdown_path, json_path = agent.write_outputs(report)

    assert markdown_path.name == "delta_W29.md"
    assert json_path.name == "delta_W29.json"
    markdown = markdown_path.read_text(encoding="utf-8")
    assert markdown.startswith("# delta_W29.md")
    assert "- Locked prediction: vW28" in markdown
    assert "- Completed actuals: W29" in markdown


def test_write_outputs_derives_week_when_actuals_label_is_missing(tmp_path):
    """Legacy payloads without a usable actuals label still file safely."""
    import dataclasses

    _write_pair(tmp_path, "W28", "W29", underscore=True)
    agent = DeltaAgent(repo_root=tmp_path)
    report = agent.run("vW28", "W29")
    legacy = dataclasses.replace(report, actuals_week="")

    markdown_path, json_path = agent.write_outputs(legacy)

    assert markdown_path.name == "delta_W29.md"
    assert json_path.name == "delta_W29.json"


def test_weights_lookback_trusts_payload_week_over_filename(tmp_path):
    """Mixed old/new file names must not skip or double-count reports.

    The directory mixes every convention the transition can produce, and the
    fixture is chosen so filename-keyed and payload-keyed selection disagree:

    * ``delta_W29.json`` - legacy prediction-week name, payload pair vW28.
    * ``delta_W30.json`` - NEW actuals-week name for the previous pair vW29.
      Filename-keyed filtering drops it (30 < 30 is false) and would regress
      the review to the older vW28 weights; payload-keyed filtering keeps it.
    * ``delta_W31.json`` - stale regeneration of the *current* vW30 pair,
      which must be excluded as not strictly earlier.

    Marker weights identify which file fed the review: 0.40 (vW29) is
    correct; 0.25 (vW28) is the filename-keyed regression.
    """
    _write_pair(tmp_path, "W30", "W31", underscore=True)
    output_dir = tmp_path / "data" / "outputs" / "delta"
    output_dir.mkdir(parents=True)
    (output_dir / "delta_W29.json").write_text(
        _weights_json("vW28", "W29", marker=0.25), encoding="utf-8"
    )
    (output_dir / "delta_W30.json").write_text(
        _weights_json("vW29", "W30", marker=0.4), encoding="utf-8"
    )
    (output_dir / "delta_W31.json").write_text(
        _weights_json("vW30", "W31", marker=0.6), encoding="utf-8"
    )

    report = DeltaAgent(repo_root=tmp_path).run("vW30", "W31")

    # marker=0.4 identifies the vW29 payload as the weights source; the
    # same-pair stale file (0.6) and the older pair (0.25) must lose.
    current = {
        item.agent: item.current_weight for item in report.weight_adjustments
    }
    assert current["almanac"] == pytest.approx(0.4)
