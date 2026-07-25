"""Load the /data Markdown archives into SQLite as ``source='archive'`` rows.

Runs at server startup when ``[database].load_file_data`` is true. Idempotent:
every entity is upserted by its natural key, so repeated startups do not create
duplicates. Per-file failures are logged and skipped so one malformed archive
never blocks startup.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict

from agents.almanac.almanac_agent import AlmanacAgent
from agents.evidence.evidence_agent import EvidenceAgent
from agents.macro.macro_agent import MacroAgent
from agents.technical.technical_agent import TechnicalAgent
from server.db import repository as repo
from server.db.context import db_session

logger = logging.getLogger(__name__)

# agent_type -> agent class exposing parse_md(text, prediction_date) -> output
_AGENT_CLASSES = {
    "almanac": AlmanacAgent,
    "macro": MacroAgent,
    "technical": TechnicalAgent,
}


def _to_payload(output) -> dict:
    """Serialize a dataclass output to a JSON-safe payload (dates, str-enums)."""
    return json.loads(json.dumps(asdict(output), default=str))


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

            for agent_type, agent_cls in _AGENT_CLASSES.items():
                path = _resolve_agent_path(agent_type, stem)
                text = _read_text(path) if path else None
                if not text:
                    continue
                try:
                    payload = _to_payload(agent_cls.parse_md(text, pred))
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
                    _to_payload(EvidenceAgent.parse_md(evidence_text, pred)),
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
