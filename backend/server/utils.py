import json
from datetime import date
from pathlib import Path

from flask import jsonify
from werkzeug.exceptions import BadRequest

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUTS_ROOT = REPO_ROOT / "data" / "outputs"


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def require_fields(body: dict, *fields: str) -> None:
    for field in fields:
        if field not in body or body[field] is None:
            raise BadRequest(f"Missing required field: {field}")


def artifact_path(
    agent_type: str,
    week_stem: str,
    run_id: str,
    *,
    horizon_days: int | None = None,
    model: str | None = None,
) -> Path:
    base = OUTPUTS_ROOT / agent_type
    if agent_type == "llm":
        filename = f"llm_{model}_{week_stem}_{run_id}_{horizon_days}d.json"
    elif agent_type == "evidence":
        filename = f"evidence_{week_stem}_{run_id}.json"
    else:
        filename = f"{agent_type}_{week_stem}_{run_id}_{horizon_days}d.json"
    return base / filename


def load_artifact(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Artifact not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def err(message: str, status: int) -> tuple:
    return jsonify({"error": message}), status
