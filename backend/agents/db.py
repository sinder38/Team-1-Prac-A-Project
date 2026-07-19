"""SQLite persistence: agents.db (no model) + llm.db (with model)."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AGENTS_DB_PATH = REPO_ROOT / "data" / "agents.db"
DEFAULT_LLM_DB_PATH = REPO_ROOT / "data" / "llm.db"
DEFAULT_HUMAN_DB_PATH = REPO_ROOT / "data" / "human.db"
HUMAN_MD_DIR = REPO_ROOT / "data" / "human"

# SQLite UNIQUE treats NULLs as distinct — use a sentinel for missing horizon.
_NO_HORIZON = -1


def agents_db_path() -> Path:
    raw = os.environ.get("AGENTS_DATABASE_PATH")
    return Path(raw) if raw else DEFAULT_AGENTS_DB_PATH


def llm_db_path() -> Path:
    raw = os.environ.get("LLM_DATABASE_PATH")
    return Path(raw) if raw else DEFAULT_LLM_DB_PATH


def human_db_path() -> Path:
    raw = os.environ.get("HUMAN_DATABASE_PATH")
    return Path(raw) if raw else DEFAULT_HUMAN_DB_PATH


def _key_horizon(horizon_days: int | None) -> int:
    return _NO_HORIZON if horizon_days is None else horizon_days


def get_agents_conn() -> sqlite3.Connection:
    path = agents_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_outputs (
            agent_type      TEXT NOT NULL,
            week_stem       TEXT NOT NULL,
            run_id          TEXT NOT NULL,
            horizon_days    INTEGER NOT NULL,
            prediction_date TEXT,
            data            TEXT NOT NULL,
            created_at      TEXT NOT NULL,
            PRIMARY KEY (agent_type, week_stem, run_id, horizon_days)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_agent_outputs_week "
        "ON agent_outputs (week_stem)"
    )
    return conn


def get_llm_conn() -> sqlite3.Connection:
    path = llm_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS llm_outputs (
            week_stem       TEXT NOT NULL,
            run_id          TEXT NOT NULL,
            horizon_days    INTEGER NOT NULL,
            model           TEXT NOT NULL,
            prediction_date TEXT,
            data            TEXT NOT NULL,
            created_at      TEXT NOT NULL,
            PRIMARY KEY (week_stem, run_id, horizon_days, model)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_llm_outputs_week "
        "ON llm_outputs (week_stem)"
    )
    return conn


def get_human_conn() -> sqlite3.Connection:
    path = human_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS human_scores (
            week_stem  TEXT NOT NULL PRIMARY KEY,
            data       TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    return conn


def save_agent_artifact(
        *,
        agent_type: str,
        week_stem: str,
        run_id: str,
        data: dict[str, Any] | str,
        horizon_days: int | None = None,
        prediction_date: date | str | None = None,
) -> None:
    payload = data if isinstance(data, str) else json.dumps(data, indent=2, default=str)
    pred = (
        prediction_date.isoformat()
        if isinstance(prediction_date, date)
        else prediction_date
    )
    now = datetime.now(timezone.utc).isoformat()
    with get_agents_conn() as conn:
        conn.execute(
            """
            INSERT INTO agent_outputs (
                agent_type, week_stem, run_id, horizon_days,
                prediction_date, data, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(agent_type, week_stem, run_id, horizon_days)
            DO UPDATE SET
                prediction_date = excluded.prediction_date,
                data = excluded.data,
                created_at = excluded.created_at
            """,
            (
                agent_type,
                week_stem,
                run_id,
                _key_horizon(horizon_days),
                pred,
                payload,
                now,
            ),
        )


def load_agent_artifact(
        *,
        agent_type: str,
        week_stem: str,
        run_id: str,
        horizon_days: int | None = None,
) -> dict[str, Any]:
    with get_agents_conn() as conn:
        row = conn.execute(
            """
            SELECT data FROM agent_outputs
            WHERE agent_type = ? AND week_stem = ? AND run_id = ?
              AND horizon_days = ?
            """,
            (agent_type, week_stem, run_id, _key_horizon(horizon_days)),
        ).fetchone()
    if row is None:
        raise FileNotFoundError(
            f"Agent artifact not found: {agent_type}/{week_stem}/{run_id}"
            f" horizon={horizon_days}"
        )
    return json.loads(row["data"])


def agent_artifact_exists(
        *,
        agent_type: str,
        week_stem: str,
        run_id: str,
        horizon_days: int | None = None,
) -> bool:
    try:
        load_agent_artifact(
            agent_type=agent_type,
            week_stem=week_stem,
            run_id=run_id,
            horizon_days=horizon_days,
        )
        return True
    except FileNotFoundError:
        return False


def save_llm_artifact(
        *,
        week_stem: str,
        run_id: str,
        model: str,
        data: dict[str, Any] | str,
        horizon_days: int,
        prediction_date: date | str | None = None,
) -> None:
    payload = data if isinstance(data, str) else json.dumps(data, indent=2, default=str)
    pred = (
        prediction_date.isoformat()
        if isinstance(prediction_date, date)
        else prediction_date
    )
    now = datetime.now(timezone.utc).isoformat()
    with get_llm_conn() as conn:
        conn.execute(
            """
            INSERT INTO llm_outputs (
                week_stem, run_id, horizon_days, model,
                prediction_date, data, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(week_stem, run_id, horizon_days, model)
            DO UPDATE SET
                prediction_date = excluded.prediction_date,
                data = excluded.data,
                created_at = excluded.created_at
            """,
            (week_stem, run_id, horizon_days, model, pred, payload, now),
        )


def load_llm_artifact(
        *,
        week_stem: str,
        run_id: str,
        model: str,
        horizon_days: int,
) -> dict[str, Any]:
    with get_llm_conn() as conn:
        row = conn.execute(
            """
            SELECT data FROM llm_outputs
            WHERE week_stem = ? AND run_id = ?
              AND horizon_days = ? AND model = ?
            """,
            (week_stem, run_id, horizon_days, model),
        ).fetchone()
    if row is None:
        raise FileNotFoundError(
            f"LLM artifact not found: {week_stem}/{run_id}"
            f" horizon={horizon_days} model={model}"
        )
    return json.loads(row["data"])


def list_run_ids(week_stem: str) -> list[str]:
    """Union of run_ids from agents.db and llm.db for a week."""
    ids: set[str] = set()
    with get_agents_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT run_id FROM agent_outputs WHERE week_stem = ?",
            (week_stem,),
        ).fetchall()
        ids.update(r["run_id"] for r in rows)
    with get_llm_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT run_id FROM llm_outputs WHERE week_stem = ?",
            (week_stem,),
        ).fetchall()
        ids.update(r["run_id"] for r in rows)
    return sorted(ids)


def save_human_score(*, week_stem: str, data: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with get_human_conn() as conn:
        conn.execute(
            """
            INSERT INTO human_scores (week_stem, data, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(week_stem)
            DO UPDATE SET
                data = excluded.data,
                created_at = excluded.created_at
            """,
            (week_stem, data, now),
        )


def load_human_score(*, week_stem: str) -> str:
    with get_human_conn() as conn:
        row = conn.execute(
            "SELECT data FROM human_scores WHERE week_stem = ?",
            (week_stem,),
        ).fetchone()
    if row is None:
        raise FileNotFoundError(f"Human score not found for {week_stem}")
    return row["data"]


def ingest_human_score_md(week_stem: str) -> bool:
    """If data/human/human_score_{week_stem}.md exists, store it. Else skip."""
    path = HUMAN_MD_DIR / f"human_score_{week_stem}.md"
    if not path.exists():
        return False  # not uploaded yet — skip, do not raise
    save_human_score(week_stem=week_stem, data=path.read_text(encoding="utf-8"))
    return True
