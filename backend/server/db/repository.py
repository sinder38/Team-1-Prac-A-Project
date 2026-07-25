"""Persistence and query helpers over the SQLite store.

All functions take an explicit ``Session`` so callers control the transaction
boundary (see ``server.db.context.db_session``).
"""

from __future__ import annotations

import re
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from server.db.models import (
    SOURCE_ARCHIVE,
    SOURCE_RUN,
    AgentOutput,
    DeltaReport,
    FinalPrediction,
    HumanScore,
    LLMComparison,
    LLMOutput,
    PredictionRun,
)


def get_runtime_run(session: Session, run_id: str) -> PredictionRun | None:
    return session.scalar(
        select(PredictionRun).where(
            PredictionRun.run_id == run_id,
            PredictionRun.source == SOURCE_RUN,
        )
    )


def get_or_create_runtime_run(
    session: Session,
    *,
    run_id: str,
    prediction_date: date,
    horizon_days: int | None,
    week_stem: str,
) -> PredictionRun:
    """Fetch the runtime run for ``run_id`` or create it.

    A run has one date and one horizon across all steps, but steps arrive in
    any order and some (evidence) carry no horizon. So a missing horizon is
    filled in by whichever step provides one; a *conflicting* date or horizon
    signals a client bug and is rejected.
    """
    run = get_runtime_run(session, run_id)
    if run is None:
        run = PredictionRun(
            run_id=run_id,
            prediction_date=prediction_date,
            horizon_days=horizon_days,
            week_stem=week_stem,
            source=SOURCE_RUN,
        )
        session.add(run)
        session.flush()
        return run

    if run.prediction_date != prediction_date:
        raise ValueError(
            f"run_id {run_id!r} already exists for date={run.prediction_date}; "
            f"cannot reuse it for date={prediction_date}"
        )
    if horizon_days is not None:
        if run.horizon_days is None:
            run.horizon_days = horizon_days
            session.flush()
        elif run.horizon_days != horizon_days:
            raise ValueError(
                f"run_id {run_id!r} already exists with horizon="
                f"{run.horizon_days}; cannot reuse it for horizon={horizon_days}"
            )
    return run


def upsert_agent_output(
    session: Session,
    run: PredictionRun,
    agent_type: str,
    payload: dict,
) -> AgentOutput:
    row = session.scalar(
        select(AgentOutput).where(
            AgentOutput.run_id_fk == run.id,
            AgentOutput.agent_type == agent_type,
        )
    )
    if row is None:
        row = AgentOutput(run_id_fk=run.id, agent_type=agent_type, payload=payload)
        session.add(row)
    else:
        row.payload = payload
    session.flush()
    return row


def get_agent_payload(
    session: Session, run_id: str, agent_type: str
) -> dict | None:
    row = session.scalar(
        select(AgentOutput)
        .join(PredictionRun, AgentOutput.run_id_fk == PredictionRun.id)
        .where(
            PredictionRun.run_id == run_id,
            PredictionRun.source == SOURCE_RUN,
            AgentOutput.agent_type == agent_type,
        )
    )
    return row.payload if row else None


def upsert_llm_output(
    session: Session,
    run: PredictionRun,
    model_slug: str,
    payload: dict,
) -> LLMOutput:
    row = session.scalar(
        select(LLMOutput).where(
            LLMOutput.run_id_fk == run.id,
            LLMOutput.model_slug == model_slug,
        )
    )
    if row is None:
        row = LLMOutput(run_id_fk=run.id, model_slug=model_slug, payload=payload)
        session.add(row)
    else:
        row.payload = payload
    session.flush()
    return row


def get_llm_payload(
    session: Session, run_id: str, model_slug: str
) -> dict | None:
    row = session.scalar(
        select(LLMOutput)
        .join(PredictionRun, LLMOutput.run_id_fk == PredictionRun.id)
        .where(
            PredictionRun.run_id == run_id,
            PredictionRun.source == SOURCE_RUN,
            LLMOutput.model_slug == model_slug,
        )
    )
    return row.payload if row else None


def list_runtime_run_ids_for_week(session: Session, week_stem: str) -> list[str]:
    rows = session.scalars(
        select(PredictionRun.run_id).where(
            PredictionRun.week_stem == week_stem,
            PredictionRun.source == SOURCE_RUN,
            PredictionRun.run_id.is_not(None),
        )
    ).all()
    return sorted({r for r in rows if r is not None})


# --- reserved for later stages (delta / comparison / human score) -------------


def upsert_llm_comparison(
    session: Session, run: PredictionRun, payload: dict
) -> LLMComparison:
    row = session.scalar(
        select(LLMComparison).where(LLMComparison.run_id_fk == run.id)
    )
    if row is None:
        row = LLMComparison(run_id_fk=run.id, payload=payload)
        session.add(row)
    else:
        row.payload = payload
    session.flush()
    return row


def upsert_human_score(
    session: Session,
    run: PredictionRun,
    payload: dict,
    *,
    total: int | None = None,
    consensus: str | None = None,
    human_call: str | None = None,
    confidence: str | None = None,
) -> HumanScore:
    row = session.scalar(
        select(HumanScore).where(HumanScore.run_id_fk == run.id)
    )
    if row is None:
        row = HumanScore(run_id_fk=run.id)
        session.add(row)
    row.payload = payload
    row.total = total
    row.consensus = consensus
    row.human_call = human_call
    row.confidence = confidence
    session.flush()
    return row


# --- archive (source='archive', keyed by week_stem) --------------------------


def get_archive_run(session: Session, week_stem: str) -> PredictionRun | None:
    return session.scalar(
        select(PredictionRun).where(
            PredictionRun.week_stem == week_stem,
            PredictionRun.source == SOURCE_ARCHIVE,
        )
    )


def get_or_create_archive_run(
    session: Session, *, week_stem: str, prediction_date: date
) -> PredictionRun:
    run = get_archive_run(session, week_stem)
    if run is None:
        run = PredictionRun(
            run_id=None,
            prediction_date=prediction_date,
            horizon_days=None,
            week_stem=week_stem,
            source=SOURCE_ARCHIVE,
        )
        session.add(run)
        session.flush()
    return run


def agent_payload_for_run(
    session: Session, run: PredictionRun, agent_type: str
) -> dict | None:
    """Fetch one agent payload for a specific run row (either source)."""
    row = session.scalar(
        select(AgentOutput).where(
            AgentOutput.run_id_fk == run.id,
            AgentOutput.agent_type == agent_type,
        )
    )
    return row.payload if row else None


def llm_outputs_for_run(
    session: Session, run: PredictionRun
) -> list[LLMOutput]:
    """All per-model LLM outputs for a run, ordered by model slug."""
    return list(
        session.scalars(
            select(LLMOutput)
            .where(LLMOutput.run_id_fk == run.id)
            .order_by(LLMOutput.model_slug)
        ).all()
    )


def llm_comparison_for_run(
    session: Session, run: PredictionRun
) -> dict | None:
    """The stored multi-model comparison payload for a run (either source)."""
    row = session.scalar(
        select(LLMComparison).where(LLMComparison.run_id_fk == run.id)
    )
    return row.payload if row else None


def human_score_for_run(
    session: Session, run: PredictionRun
) -> dict | None:
    """The stored human-score payload for a run (either source)."""
    row = session.scalar(
        select(HumanScore).where(HumanScore.run_id_fk == run.id)
    )
    return row.payload if row else None


def get_archive_agent_payload(
    session: Session, week_stem: str, agent_type: str
) -> dict | None:
    row = session.scalar(
        select(AgentOutput)
        .join(PredictionRun, AgentOutput.run_id_fk == PredictionRun.id)
        .where(
            PredictionRun.week_stem == week_stem,
            PredictionRun.source == SOURCE_ARCHIVE,
            AgentOutput.agent_type == agent_type,
        )
    )
    return row.payload if row else None


def get_archive_llm_comparison(session: Session, week_stem: str) -> dict | None:
    row = session.scalar(
        select(LLMComparison)
        .join(PredictionRun, LLMComparison.run_id_fk == PredictionRun.id)
        .where(
            PredictionRun.week_stem == week_stem,
            PredictionRun.source == SOURCE_ARCHIVE,
        )
    )
    return row.payload if row else None


def get_archive_human_score(session: Session, week_stem: str) -> HumanScore | None:
    return session.scalar(
        select(HumanScore)
        .join(PredictionRun, HumanScore.run_id_fk == PredictionRun.id)
        .where(
            PredictionRun.week_stem == week_stem,
            PredictionRun.source == SOURCE_ARCHIVE,
        )
    )


def get_runtime_human_score(session: Session, run_id: str) -> HumanScore | None:
    return session.scalar(
        select(HumanScore)
        .join(PredictionRun, HumanScore.run_id_fk == PredictionRun.id)
        .where(
            PredictionRun.run_id == run_id,
            PredictionRun.source == SOURCE_RUN,
        )
    )


def upsert_final_prediction(
    session: Session,
    run: PredictionRun,
    payload: dict,
) -> FinalPrediction:
    row = session.scalar(
        select(FinalPrediction).where(FinalPrediction.run_id_fk == run.id)
    )
    if row is None:
        row = FinalPrediction(run_id_fk=run.id)
        session.add(row)
    row.payload = payload
    session.flush()
    return row


def get_runtime_final_prediction(session: Session, run_id: str) -> FinalPrediction | None:
    return session.scalar(
        select(FinalPrediction)
        .join(PredictionRun, FinalPrediction.run_id_fk == PredictionRun.id)
        .where(
            PredictionRun.run_id == run_id,
            PredictionRun.source == SOURCE_RUN,
        )
    )


def final_prediction_for_run(
    session: Session, run: PredictionRun
) -> dict | None:
    """The stored final-prediction payload for a run (either source)."""
    row = session.scalar(
        select(FinalPrediction).where(FinalPrediction.run_id_fk == run.id)
    )
    return row.payload if row else None


def get_runtime_run_with_final_prediction_for_week(
    session: Session, week_stem: str
) -> PredictionRun | None:
    """Any runtime run in this week that already has a locked final prediction."""
    return session.scalar(
        select(PredictionRun)
        .join(FinalPrediction, FinalPrediction.run_id_fk == PredictionRun.id)
        .where(
            PredictionRun.week_stem == week_stem,
            PredictionRun.source == SOURCE_RUN,
        )
        .limit(1)
    )


def list_runs(session: Session, source: str | None = None) -> list[PredictionRun]:
    stmt = select(PredictionRun)
    if source is not None:
        stmt = stmt.where(PredictionRun.source == source)
    return list(session.scalars(stmt).all())


def add_delta_report(
    session: Session,
    run: PredictionRun | None,
    *,
    prediction_week: str | None,
    schema_version: int | None,
    payload: dict,
) -> DeltaReport:
    row = DeltaReport(
        run_id_fk=run.id if run else None,
        prediction_week=prediction_week,
        schema_version=schema_version,
        payload=payload,
    )
    session.add(row)
    session.flush()
    return row


def get_latest_delta(session: Session) -> DeltaReport | None:
    """Latest valid (schema_version == 2) delta report by prediction week.

    Mirrors the previous file-based selection: newest prediction week wins,
    with creation time as the tiebreaker for repeated scorings of a week.
    """
    rows = list(
        session.scalars(
            select(DeltaReport).where(DeltaReport.schema_version == 2)
        ).all()
    )

    def _sort_key(row: DeltaReport) -> tuple[int, object]:
        match = re.match(r"[vW]*W?(\d+)", row.prediction_week or "")
        week_number = int(match.group(1)) if match else -1
        return (week_number, row.created_at)

    return max(rows, key=_sort_key, default=None)
