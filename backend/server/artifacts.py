import re
from collections.abc import Mapping

from agents.io import week_stem
from flask import Blueprint, jsonify, request

from server.archive import list_all_weeks, load_archive_week, load_human_score
from server.utils import OUTPUTS_ROOT, artifact_path, err, load_artifact, parse_date

artifacts_bp = Blueprint("artifacts", __name__, url_prefix="/artifacts")


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

    horizon_days = None
    if needs_horizon:
        horizon_days, error = _get_horizon_days(request.args)
        if error:
            return error

    stem, error = _stem_from_args()
    if error:
        return error

    path = artifact_path(
        agent_type,
        stem,
        run_id,
        horizon_days=horizon_days,
        model=model,
    )
    try:
        data = load_artifact(path)
    except FileNotFoundError as exc:
        return err(str(exc), 404)
    return jsonify(data), 200


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
    if not OUTPUTS_ROOT.exists():
        return jsonify({"prediction_date": raw_date, "week": stem, "run_ids": []}), 200
    run_ids: set[str] = set()

    # Scan all agent folders for artifact names containing this week.
    stem_escaped = re.escape(stem)
    standard_pattern = re.compile(
        rf"^[a-z]+_{stem_escaped}_(.+?)(?:_\d+d|_[a-z]+_\d+d)?\.json$"
    )
    llm_pattern = re.compile(rf"^llm_[a-z0-9]+_{stem_escaped}_(.+?)_\d+d\.json$")

    for subdir in OUTPUTS_ROOT.iterdir():
        if not subdir.is_dir():
            continue
        for path in subdir.glob(f"*_{stem}_*.json"):
            match = standard_pattern.match(path.name)
            if not match:
                match = llm_pattern.match(path.name)
            if match:
                run_ids.add(match.group(1))

    return (
        jsonify(
            {
                "prediction_date": raw_date,
                "week": stem,
                "run_ids": sorted(run_ids),
            }
        ),
        200,
    )


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
