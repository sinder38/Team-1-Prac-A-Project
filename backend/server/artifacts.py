import re

from flask import Blueprint, jsonify, request

from agents.io import week_stem
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


def _get_horizon_days(args: dict) -> tuple[int, tuple | None]:
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


@artifacts_bp.route("/almanac", methods=["GET"])
def get_almanac():
    run_id = request.args.get("run_id")
    if not run_id:
        return err("Missing required query param: run_id", 400)
    horizon_days, error = _get_horizon_days(request.args)
    if error:
        return error
    stem, error = _stem_from_args()
    if error:
        return error
    try:
        data = load_artifact(artifact_path("almanac", stem, run_id, horizon_days=horizon_days))
    except FileNotFoundError as e:
        return err(str(e), 404)
    return jsonify(data), 200


@artifacts_bp.route("/technical", methods=["GET"])
def get_technical():
    run_id = request.args.get("run_id")
    if not run_id:
        return err("Missing required query param: run_id", 400)
    horizon_days, error = _get_horizon_days(request.args)
    if error:
        return error
    stem, error = _stem_from_args()
    if error:
        return error
    try:
        data = load_artifact(artifact_path("technical", stem, run_id, horizon_days=horizon_days))
    except FileNotFoundError as e:
        return err(str(e), 404)
    return jsonify(data), 200


@artifacts_bp.route("/macro", methods=["GET"])
def get_macro():
    run_id = request.args.get("run_id")
    if not run_id:
        return err("Missing required query param: run_id", 400)
    horizon_days, error = _get_horizon_days(request.args)
    if error:
        return error
    stem, error = _stem_from_args()
    if error:
        return error
    try:
        data = load_artifact(artifact_path("macro", stem, run_id, horizon_days=horizon_days))
    except FileNotFoundError as e:
        return err(str(e), 404)
    return jsonify(data), 200


@artifacts_bp.route("/evidence", methods=["GET"])
def get_evidence():
    run_id = request.args.get("run_id")
    if not run_id:
        return err("Missing required query param: run_id", 400)
    stem, error = _stem_from_args()
    if error:
        return error
    try:
        data = load_artifact(artifact_path("evidence", stem, run_id))
    except FileNotFoundError as e:
        return err(str(e), 404)
    return jsonify(data), 200


@artifacts_bp.route("/llm", methods=["GET"])
def get_llm():
    run_id = request.args.get("run_id")
    if not run_id:
        return err("Missing required query param: run_id", 400)
    model = request.args.get("model")
    if not model:
        return err("Missing required query param: model", 400)
    horizon_days, error = _get_horizon_days(request.args)
    if error:
        return error
    stem, error = _stem_from_args()
    if error:
        return error
    try:
        data = load_artifact(artifact_path("llm", stem, run_id, model=model, horizon_days=horizon_days))
    except FileNotFoundError as e:
        return err(str(e), 404)
    return jsonify(data), 200


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
    run_ids: set[str] = set()

    # Scan all agent subdirectories for files matching the week stem.
    # Filename pattern: {agent_type}_{stem}_{run_id}[_{suffix}].json
    pattern = re.compile(rf"^[a-z]+_{re.escape(stem)}_(.+?)(?:_\d+d|_[a-z]+_\d+d)?\.json$")
    for subdir in OUTPUTS_ROOT.iterdir():
        if not subdir.is_dir():
            continue
        for f in subdir.glob(f"*_{stem}_*.json"):
            m = pattern.match(f.name)
            if m:
                run_ids.add(m.group(1))

    return jsonify({
        "prediction_date": raw_date,
        "week": stem,
        "run_ids": sorted(run_ids),
    }), 200
