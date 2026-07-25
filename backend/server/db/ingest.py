"""Load the /data Markdown archives into SQLite as ``source='archive'`` rows.

Runs at server startup when ``[database].load_file_data`` is true. Idempotent:
every entity is upserted by its natural key, so repeated startups do not create
duplicates. Per-file failures are logged and skipped so one malformed archive
never blocks startup.
"""

from __future__ import annotations

import logging

from server.db import parsers, repository as repo
from server.db.context import db_session

logger = logging.getLogger(__name__)

# agent_type -> parser(text, prediction_date)
_AGENT_PARSERS = {
    "almanac": parsers.parse_almanac,
    "macro": parsers.parse_macro,
    "technical": parsers.parse_technical,
}


def ingest_data_dir() -> dict[str, int]:
    """Ingest every discoverable archive week. Returns simple counts."""
    # Imported here to avoid a heavy import at module load and any cycle.
    from server.archive import (
        _human_score,
        _parse_llm_comparison,
        _read_text,
        _resolve_agent_path,
        discover_archive_stems,
    )

    counts = {"weeks": 0, "agents": 0, "llm": 0, "human": 0, "errors": 0}
    stems = discover_archive_stems()

    with db_session() as session:
        for stem, pred in stems.items():
            run = repo.get_or_create_archive_run(
                session, week_stem=stem, prediction_date=pred
            )
            counts["weeks"] += 1

            for agent_type, parser in _AGENT_PARSERS.items():
                path = _resolve_agent_path(agent_type, stem)
                text = _read_text(path) if path else None
                if not text:
                    continue
                try:
                    payload = parser(text, pred)
                except Exception as exc:  # noqa: BLE001 - keep startup resilient
                    logger.warning("ingest: %s %s failed: %s", agent_type, stem, exc)
                    counts["errors"] += 1
                    continue
                repo.upsert_agent_output(session, run, agent_type, payload)
                counts["agents"] += 1

            evidence_path = _resolve_agent_path("evidence", stem)
            evidence_text = _read_text(evidence_path) if evidence_path else None
            if evidence_text:
                repo.upsert_agent_output(
                    session,
                    run,
                    "evidence",
                    parsers.parse_evidence(evidence_text, pred, stem),
                )
                counts["agents"] += 1

            try:
                comparison = _parse_llm_comparison(stem)
            except Exception as exc:  # noqa: BLE001
                logger.warning("ingest: llm comparison %s failed: %s", stem, exc)
                comparison = None
                counts["errors"] += 1
            if comparison:
                repo.upsert_llm_comparison(session, run, comparison)
                counts["llm"] += 1

            try:
                human = _human_score(stem, pred)
            except Exception as exc:  # noqa: BLE001
                logger.warning("ingest: human score %s failed: %s", stem, exc)
                human = None
                counts["errors"] += 1
            if human:
                # Structured store: drop the redundant raw markdown snapshot.
                human.pop("rawMarkdown", None)
                form = human.get("form", {})
                repo.upsert_human_score(
                    session,
                    run,
                    human,
                    total=human.get("total"),
                    consensus=human.get("consensus"),
                    human_call=form.get("humanCall"),
                    confidence=form.get("confidence"),
                )
                counts["human"] += 1

    logger.info("ingest complete: %s", counts)
    return counts
