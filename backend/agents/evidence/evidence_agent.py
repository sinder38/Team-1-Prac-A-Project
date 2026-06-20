"""Evidence Agent — reads actuals_W{N}.md from data/evidence/ for the requested week."""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.base import BaseAgent
from agents.io import week_stem
from agents.schemas import EvidenceOutput

REPO_ROOT = Path(__file__).resolve().parents[3]


class EvidenceAgent(BaseAgent):
    agent_type = "evidence"

    def __init__(self, data_root: Path | None = None):
        self._data_root = data_root or REPO_ROOT / "data"

    def run(self, prediction_date: date, **kwargs) -> EvidenceOutput:
        week = week_stem(prediction_date)
        path = self._data_root / "evidence" / f"actuals_{week}.md"
        if not path.exists():
            raise FileNotFoundError(
                f"Evidence file not found for {week}: expected {path}"
            )
        content = path.read_text(encoding="utf-8")
        return EvidenceOutput(
            prediction_date=prediction_date,
            week=week,
            content=content,
        )

    def render_md(self, output: EvidenceOutput, prediction_date: date) -> str:
        return output.content
