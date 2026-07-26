"""SQLAlchemy ORM models — the datacentric store for server runtime data.

Design (see migration plan):

* ``PredictionRun`` is the spine. A run has exactly one ``prediction_date`` and
  one ``horizon_days`` across all its steps. Runtime runs are identified by
  ``run_id``; archive rows loaded from ``/data`` are identified by ``week_stem``.
  Two partial unique indexes enforce the two distinct identities.
* Every child hangs off a run and stores a single structured ``payload`` JSON
  (the parsed agent-schema fields). No raw markdown is stored — ``.md``
  artifacts are regenerated on request from the payload.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

SOURCE_RUN = "run"
SOURCE_ARCHIVE = "archive"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class PredictionRun(Base):
    """One prediction instance. Spine for all artifacts."""

    __tablename__ = "prediction_run"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Runtime identity. NULL for archive-sourced rows.
    run_id: Mapped[str | None] = mapped_column(String, nullable=True)
    prediction_date: Mapped[date] = mapped_column(Date, nullable=False)
    # The run's single horizon. NULL for archive-sourced rows.
    horizon_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Derived label (e.g. "W25"). Identity for archive-sourced rows only.
    week_stem: Mapped[str | None] = mapped_column(String, nullable=True)
    source: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    agent_outputs: Mapped[list["AgentOutput"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    llm_outputs: Mapped[list["LLMOutput"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    llm_comparison: Mapped["LLMComparison | None"] = relationship(
        back_populates="run", cascade="all, delete-orphan", uselist=False
    )
    human_score: Mapped["HumanScore | None"] = relationship(
        back_populates="run", cascade="all, delete-orphan", uselist=False
    )
    final_prediction: Mapped["FinalPrediction | None"] = relationship(
        back_populates="run", cascade="all, delete-orphan", uselist=False
    )
    delta_reports: Mapped[list["DeltaReport"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # A runtime run is identified by its run_id.
        Index(
            "uq_run_runtime_run_id",
            "run_id",
            unique=True,
            sqlite_where=text(f"source = '{SOURCE_RUN}'"),
        ),
        # The /data archive has exactly one weekly entry per stem.
        Index(
            "uq_run_archive_week_stem",
            "week_stem",
            unique=True,
            sqlite_where=text(f"source = '{SOURCE_ARCHIVE}'"),
        ),
        Index("ix_run_date_horizon", "prediction_date", "horizon_days"),
    )


class AgentOutput(Base):
    """Almanac / macro / technical / evidence structured output."""

    __tablename__ = "agent_output"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id_fk: Mapped[int] = mapped_column(
        ForeignKey("prediction_run.id", ondelete="CASCADE"), nullable=False
    )
    agent_type: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    run: Mapped[PredictionRun] = relationship(back_populates="agent_outputs")

    __table_args__ = (
        UniqueConstraint("run_id_fk", "agent_type", name="uq_agent_per_run"),
    )


class LLMOutput(Base):
    """One LLM model's structured synthesis output."""

    __tablename__ = "llm_output"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id_fk: Mapped[int] = mapped_column(
        ForeignKey("prediction_run.id", ondelete="CASCADE"), nullable=False
    )
    model_slug: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    run: Mapped[PredictionRun] = relationship(back_populates="llm_outputs")

    __table_args__ = (
        UniqueConstraint("run_id_fk", "model_slug", name="uq_llm_per_run"),
    )


class LLMComparison(Base):
    """Per-run multi-model comparison (regenerable from LLMOutput rows)."""

    __tablename__ = "llm_comparison"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id_fk: Mapped[int] = mapped_column(
        ForeignKey("prediction_run.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    run: Mapped[PredictionRun] = relationship(back_populates="llm_comparison")


class HumanScore(Base):
    """Team human-score report. ``payload`` holds the full parsed form."""

    __tablename__ = "human_score"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id_fk: Mapped[int] = mapped_column(
        ForeignKey("prediction_run.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    # Promoted for cheap querying / display without opening the payload.
    total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    consensus: Mapped[str | None] = mapped_column(String, nullable=True)
    human_call: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence: Mapped[str | None] = mapped_column(String, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    run: Mapped[PredictionRun] = relationship(back_populates="human_score")


class FinalPrediction(Base):
    """Team locked consensus brief. ``payload`` is the structured form + markdown."""

    __tablename__ = "final_prediction"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id_fk: Mapped[int] = mapped_column(
        ForeignKey("prediction_run.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    run: Mapped[PredictionRun] = relationship(back_populates="final_prediction")


class DeltaReport(Base):
    """Delta Engine scoring of a previous week against current actuals."""

    __tablename__ = "delta_report"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id_fk: Mapped[int | None] = mapped_column(
        ForeignKey("prediction_run.id", ondelete="CASCADE"), nullable=True
    )
    prediction_week: Mapped[str | None] = mapped_column(String, nullable=True)
    schema_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    run: Mapped[PredictionRun | None] = relationship(back_populates="delta_reports")
