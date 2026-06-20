import pytest
from datetime import date
from pathlib import Path

from agents.evidence.evidence_agent import EvidenceAgent
from agents.schemas import EvidenceOutput


def test_run_returns_evidence_output(tmp_path):
    # Set up a fake evidence file
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    (evidence_dir / "actuals_W25.md").write_text("# Week 25\nSPX up 1%", encoding="utf-8")

    agent = EvidenceAgent(data_root=tmp_path)
    result = agent.run(date(2026, 6, 16))

    assert isinstance(result, EvidenceOutput)
    assert result.week == "W25"
    assert result.content == "# Week 25\nSPX up 1%"
    assert result.prediction_date == date(2026, 6, 16)
    assert result.agent_type == "evidence"


def test_run_raises_on_missing_file(tmp_path):
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()

    agent = EvidenceAgent(data_root=tmp_path)
    with pytest.raises(FileNotFoundError, match="actuals_W25.md"):
        agent.run(date(2026, 6, 16))


def test_run_uses_correct_week_filename(tmp_path):
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    # date(2026, 6, 16) is W25
    (evidence_dir / "actuals_W25.md").write_text("W25 content", encoding="utf-8")

    agent = EvidenceAgent(data_root=tmp_path)
    result = agent.run(date(2026, 6, 16))
    assert result.week == "W25"
    assert result.content == "W25 content"
