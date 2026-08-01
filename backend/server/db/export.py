"""Regenerate Markdown artifacts from the DB on request.

This backs ``POST /export`` — e.g. after a successful pipeline run, produce the
``.md``/``.txt`` files from the stored structured data:

* the four agents (almanac, macro, technical, evidence),
* the Delta Engine report,
* per-model LLM synthesis files (``synthesis_<slug>_<stem>.txt``),
* the multi-model comparison (``llm_comparison_<stem>.md``),
* the team human score (``human_score_<stem>.md``).

Only artifacts actually stored for the run are emitted. Technical output and the
archive-sourced comparison/human-score are lossy (see ``server.db.render``).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from agents.delta.parsing import plain_week
from agents.io import week_stem
from agents.paths import DATA_DIR
from server.db import render
from server.db import repository as repo
from server.db.models import PredictionRun

# agent_type -> (subdirectory under data/, filename template)
_EXPORTABLE = ("almanac", "macro", "technical", "evidence")


def _filename(agent_type: str, stem: str) -> str:
    if agent_type == "evidence":
        return f"actuals_{stem}.md"
    return f"{agent_type}_agent_{stem}.md"


def _artifact(agent_type: str, directory: str, filename: str, markdown: str) -> dict:
    return {
        "agent_type": agent_type,
        "directory": directory,
        "filename": filename,
        "markdown": markdown,
    }


def build_run_artifacts(session: Session, run: PredictionRun) -> list[dict]:
    """Render every artifact stored for ``run``: agents, LLM synthesis, the
    multi-model comparison, and the human score."""
    stem = run.week_stem or week_stem(run.prediction_date)
    pred = run.prediction_date
    artifacts: list[dict] = []

    # TODO: not the the best way to handle export.
    # It would be better to create a more unified system for all agents/llm/human/etc to do export
    for agent_type in _EXPORTABLE:
        payload = repo.agent_payload_for_run(session, run, agent_type)
        if not payload:
            continue
        artifacts.append(
            _artifact(
                agent_type,
                agent_type,
                _filename(agent_type, stem),
                render.render_markdown(agent_type, payload),
            )
        )

    artifacts += _llm_artifacts(session, run, stem, pred)

    human = repo.human_score_for_run(session, run)
    if human:
        artifacts.append(
            _artifact(
                "human_score",
                "human",
                f"human_score_{stem}.md",
                render.render_human_score(human),
            )
        )

    final = repo.final_prediction_for_run(session, run)
    if final:
        week = str(final.get("week") or stem)
        artifacts.append(
            _artifact(
                "final_prediction",
                "final prediction",
                f"prediction_{week}_Team1.md",
                render.render_final_prediction(final),
            )
        )

    delta = repo.delta_report_for_run(session, run)
    if delta:
        delta_stem = plain_week(delta.prediction_week or "")
        artifacts.append(
            _artifact(
                "delta",
                "qa",
                f"delta_{delta_stem}.md",
                render.render_delta(delta.payload),
            )
        )

    return artifacts


def _llm_artifacts(
    session: Session, run: PredictionRun, stem: str, pred: date
) -> list[dict]:
    """Per-model synthesis files plus the comparison table.

    Prefers the run's per-model LLM outputs (lossless). Falls back to the parsed
    comparison payload when only that is stored (archive weeks)."""
    artifacts: list[dict] = []
    llm_rows = repo.llm_outputs_for_run(session, run)

    for row in llm_rows:
        artifacts.append(
            _artifact(
                "llm_synthesis",
                "llm",
                f"synthesis_{row.model_slug}_{stem}.txt",
                render.render_llm_synthesis(row.payload),
            )
        )

    if llm_rows:
        markdown = render.render_llm_comparison_from_outputs(
            [(row.model_slug, row.payload) for row in llm_rows], stem, pred
        )
        artifacts.append(
            _artifact("llm_comparison", "llm", f"llm_comparison_{stem}.md", markdown)
        )
        return artifacts

    comparison = repo.llm_comparison_for_run(session, run)
    if comparison:
        markdown = render.render_llm_comparison_from_payload(comparison, stem, pred)
        artifacts.append(
            _artifact("llm_comparison", "llm", f"llm_comparison_{stem}.md", markdown)
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
