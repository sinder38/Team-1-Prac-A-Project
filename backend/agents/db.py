"""SQLite persistence for agent raw outputs (replaces data/outputs/*.json)."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = REPO_ROOT / "data" / "predictions.db"

# SQLite UNIQUE treats NULLs as distinct — use sentinels in the key columns.
_NO_HORIZON = -1
_NO_MODEL = ""


def db_path() -> Path:
    raw = os.environ.get("DATABASE_PATH")
    return Path(raw) if raw else DEFAULT_DB_PATH


def get_conn() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_outputs (
                agent_type      TEXT NOT NULL,
                week_stem       TEXT NOT NULL,
                run_id          TEXT NOT NULL,
                horizon_days    INTEGER NOT NULL,
                model           TEXT NOT NULL,
                prediction_date TEXT,
                data            TEXT NOT NULL,
                created_at      TEXT NOT NULL,
                PRIMARY KEY (agent_type, week_stem, run_id, horizon_days, model)
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_agent_outputs_week "
            "ON agent_outputs (week_stem)"
        )


def _key_horizon(horizon_days: int | None) -> int:
    return _NO_HORIZON if horizon_days is None else horizon_days


def _key_model(model: str | None) -> str:
    return _NO_MODEL if model is None else model


def save_artifact(
    *,
    agent_type: str,
    week_stem: str,
    run_id: str,
    data: dict[str, Any] | str,
    horizon_days: int | None = None,
    model: str | None = None,
    prediction_date: date | str | None = None,
) -> None:
    init_db()
    payload = data if isinstance(data, str) else json.dumps(data, indent=2, default=str)
    pred = (
        prediction_date.isoformat()
        if isinstance(prediction_date, date)
        else prediction_date
    )
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO agent_outputs (
                agent_type, week_stem, run_id, horizon_days, model,
                prediction_date, data, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(agent_type, week_stem, run_id, horizon_days, model)
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
                _key_model(model),
                pred,
                payload,
                now,
            ),
        )


def load_artifact(
    *,
    agent_type: str,
    week_stem: str,
    run_id: str,
    horizon_days: int | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    init_db()
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT data FROM agent_outputs
            WHERE agent_type = ? AND week_stem = ? AND run_id = ?
              AND horizon_days = ? AND model = ?
            """,
            (
                agent_type,
                week_stem,
                run_id,
                _key_horizon(horizon_days),
                _key_model(model),
            ),
        ).fetchone()
    if row is None:
        raise FileNotFoundError(
            f"Artifact not found: {agent_type}/{week_stem}/{run_id}"
            f" horizon={horizon_days} model={model}"
        )
    return json.loads(row["data"])


def artifact_exists(
    *,
    agent_type: str,
    week_stem: str,
    run_id: str,
    horizon_days: int | None = None,
    model: str | None = None,
) -> bool:
    try:
        load_artifact(
            agent_type=agent_type,
            week_stem=week_stem,
            run_id=run_id,
            horizon_days=horizon_days,
            model=model,
        )
        return True
    except FileNotFoundError:
        return False


def list_run_ids(week_stem: str) -> list[str]:
    init_db()
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT run_id FROM agent_outputs
            WHERE week_stem = ?
            ORDER BY run_id
            """,
            (week_stem,),
        ).fetchall()
    return [r["run_id"] for r in rows]