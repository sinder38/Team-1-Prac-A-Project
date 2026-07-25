"""Regenerate Markdown artifacts from the DB on request.

This backs ``POST /export`` — e.g. after a successful pipeline run, produce the
per-agent ``.md`` files from the stored structured data. Technical output is
lossy (see ``server.db.render``); the LLM comparison and human score have no
Markdown renderer and are not exported here.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from agents.io import week_stem
from agents.paths import DATA_DIR
from server.db import render, repository as repo
from server.db.models import PredictionRun

# agent_type -> (subdirectory under data/, filename template)
_EXPORTABLE = ("almanac", "macro", "technical", "evidence")


def _filename(agent_type: str, stem: str) -> str:
    if agent_type == "evidence":
        return f"actuals_{stem}.md"
    return f"{agent_type}_agent_{stem}.md"


def build_run_artifacts(session: Session, run: PredictionRun) -> list[dict]:
    """Render every exportable agent artifact stored for ``run``."""
    stem = run.week_stem or week_stem(run.prediction_date)
    artifacts: list[dict] = []
    for agent_type in _EXPORTABLE:
        payload = repo.agent_payload_for_run(session, run, agent_type)
        if not payload:
            continue
        artifacts.append(
            {
                "agent_type": agent_type,
                "directory": agent_type,
                "filename": _filename(agent_type, stem),
                "markdown": render.render_markdown(agent_type, payload),
            }
        )
    return artifacts


def write_artifacts(artifacts: list[dict], data_dir: Path = DATA_DIR) -> list[str]:
    """Write rendered artifacts to data/<agent>/<filename>. Returns the paths."""
    written: list[str] = []
    for art in artifacts:
        out_dir = data_dir / art["directory"]
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / art["filename"]
        path.write_text(art["markdown"], encoding="utf-8")
        written.append(str(path))
    return written
