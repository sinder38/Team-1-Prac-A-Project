import re
from collections.abc import Mapping

from agents.io import week_stem
from flask import Blueprint, jsonify, request

from server.archive import list_all_weeks, load_archive_week, load_human_score
from server.db import repository as repo
from server.db.context import db_session
from server.utils import err, parse_date

artifacts_bp = Blueprint("artifacts", __name__, url_prefix="/artifacts")


@artifacts_bp.route("/almanac", methods=["GET"])
def get_almanac():
    return _saved_artifact_response("almanac", needs_horizon=True)


@artifacts_bp.route("/technical", methods=["GET"])
def get_technical():
    return _saved_artifact_response("technical", needs_horizon=True)


@artifacts_bp.route("/macro", methods=["GET"])
def get_macro():
    return _saved_artifact_response("macro", needs_horizon=True)


@artifacts_bp.route("/evidence", methods=["GET"])
def get_evidence():
    return _saved_artifact_response("evidence")


@artifacts_bp.route("/llm", methods=["GET"])
def get_llm():
    return _saved_artifact_response(
        "llm",
        needs_horizon=True,
        needs_model=True,
    )


@artifacts_bp.route("/runs", methods=["GET"])
def get_runs():
    raw_date = request.args.get("prediction_date")
    if not raw_date:
        return err("Missing required query param: prediction_date", 400)
    try:
        prediction_date = parse_date(raw_date)
    except ValueError:
        return err(f"Invalid prediction_date: {raw_date!r}", 400)

    stem = week_stem(prediction_date)
    with db_session() as session:
        run_ids = repo.list_runtime_run_ids_for_week(session, stem)

    return (
        jsonify(
            {
                "prediction_date": raw_date,
                "week": stem,
                "run_ids": run_ids,
            }
        ),
        200,
    )



@artifacts_bp.route("/weeks", methods=["GET"])
def list_weeks():
    return jsonify({"weeks": list_all_weeks()}), 200


@artifacts_bp.route("/archive", methods=["GET"])
def get_archive():
    raw_stem = request.args.get("stem") or request.args.get("week")
    stem, error = _normalize_week_stem(raw_stem)
    if error:
        return error
    if stem is None:
        return err("Missing required query param: stem (e.g. W25)", 400)
    try:
        payload = load_archive_week(stem)
    except ValueError as exc:
        return err(str(exc), 400)
    if payload is None:
        return err(f"No archive data for {stem}", 404)
    return jsonify(payload), 200


@artifacts_bp.route("/human-score", methods=["GET"])
def get_human_score():
    raw_stem = request.args.get("stem") or request.args.get("week")
    stem, error = _normalize_week_stem(raw_stem)
    if error:
        return error
    if stem is None:
        return err("Missing required query param: stem (e.g. W25)", 400)
    try:
        payload = load_human_score(stem)
    except ValueError as exc:
        return err(str(exc), 400)
    if payload is None:
        return err(f"No human score archive for {stem}", 404)
    return jsonify(payload), 200

def _stem_from_args() -> tuple[str, tuple | None]:
    """Extract week_stem from prediction_date query param.

    Returns (stem, None) on success, or ("", error_response) on failure.
    """
    raw = request.args.get("prediction_date")
    if not raw:
        return "", err("Missing required query param: prediction_date", 400)
    try:
        return week_stem(parse_date(raw)), None
    except ValueError:
        return "", err(f"Invalid prediction_date: {raw!r}", 400)


def _get_horizon_days(args: Mapping[str, str]) -> tuple[int, tuple | None]:
    raw = args.get("horizon_days")
    if raw is None:
        return 0, err("Missing required query param: horizon_days", 400)
    try:
        val = int(raw)
        if val <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return 0, err("horizon_days must be a positive integer", 400)
    return val, None


def _saved_artifact_response(
    agent_type: str,
    *,
    needs_horizon: bool = False,
    needs_model: bool = False,
):
    """Load one saved pipeline artifact from the request query values."""
    run_id = request.args.get("run_id")
    if not run_id:
        return err("Missing required query param: run_id", 400)

    model = None
    if needs_model:
        model = request.args.get("model")
        if not model:
            return err("Missing required query param: model", 400)

    if needs_horizon:
        _horizon_days, error = _get_horizon_days(request.args)
        if error:
            return error

    # prediction_date is validated for API compatibility; the DB locates the
    # artifact by run_id, so the stem itself is no longer needed here.
    _stem, error = _stem_from_args()
    if error:
        return error

    with db_session() as session:
        if agent_type == "llm":
            if model is None:
                return err("Missing required query param: model", 400)
            data = repo.get_llm_payload(session, run_id, model)
        else:
            data = repo.get_agent_payload(session, run_id, agent_type)
    if data is None:
        return err(
            f"Artifact not found: {agent_type} for run_id={run_id!r}", 404
        )
    return jsonify(data), 200

# Past weeks include generated JSON runs and older Markdown archives.
def _normalize_week_stem(raw: str | None) -> tuple[str | None, tuple | None]:
    """Parse stem query param. Accepts W25 or 2026-W25. Returns (stem, error)."""
    if not raw:
        return None, err("Missing required query param: stem (e.g. W25)", 400)
    stem = raw.strip().upper()
    if re.fullmatch(r"\d{4}-W\d{2}", stem):
        stem = stem.split("-")[1]
    if not re.fullmatch(r"W\d{2}", stem):
        return None, err(f"Invalid stem: {raw!r} (expected W25 or 2026-W25)", 400)
    return stem, None
