import re
from collections.abc import Mapping
from pathlib import Path

from agents.delta.parsing import parse_actuals_file
from agents.io import week_stem
from agents.paths import DATA_DIR
from flask import Blueprint, jsonify, request, send_from_directory

from server.archive import list_all_weeks, load_archive_week, load_human_score
from server.db import repository as repo
from server.db.context import db_session
from server.utils import err, parse_date

artifacts_bp = Blueprint("artifacts", __name__, url_prefix="/artifacts")

_EVIDENCE_DIR = DATA_DIR / "evidence"
_EVIDENCE_FILE_RE = re.compile(r"^finviz_[A-Za-z0-9._-]+\.png$")


def _evidence_image_label(name: str) -> str:
    lower = name.lower()
    if "sectors" in lower:
        return "Sector performance (5D)"
    if "1w" in lower:
        return "Index performance (1W)"
    return name


@artifacts_bp.route("/actuals", methods=["GET"])
def get_actuals():
    """Parse data/evidence/actuals_{stem}.md into { asset: move_pct }."""
    raw_stem = request.args.get("stem") or request.args.get("week")
    stem, error = _normalize_week_stem(raw_stem)
    if error:
        return error

    path = _EVIDENCE_DIR / f"actuals_{stem}.md"
    if not path.is_file():
        return jsonify({"stem": stem, "assets": {}}), 200
    try:
        rows = parse_actuals_file(path)
    except (ValueError, FileNotFoundError) as exc:
        return err(str(exc), 400)
    return jsonify({
        "stem": stem,
        "assets": {
            asset: {"move_pct": row.actual_move, "direction": row.actual_direction}
            for asset, row in rows.items()
        },
    }), 200


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


@artifacts_bp.route("/llm-comparison", methods=["GET"])
def get_llm_comparison():
    """All LLM outputs for a runtime run (or a stored comparison payload)."""
    run_id = request.args.get("run_id")
    if not run_id:
        return err("Missing required query param: run_id", 400)

    with db_session() as session:
        run = repo.get_runtime_run(session, str(run_id))
        if run is None:
            return err(f"Unknown run_id={run_id!r}", 404)

        stored = repo.llm_comparison_for_run(session, run)
        models = stored.get("models") if isinstance(stored, dict) else None
        if isinstance(models, list) and models:
            return jsonify({"comparison": stored, "source": "stored"}), 200

        rows = repo.llm_outputs_for_run(session, run)
        if not rows:
            return err(f"No LLM outputs for run_id={run_id!r}", 404)

        models = [
            {
                "slug": row.model_slug,
                "name": (row.payload or {}).get("model_name") or row.model_slug,
                "data": row.payload,
            }
            for row in rows
        ]
    return jsonify({"models": models, "source": "outputs"}), 200


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



@artifacts_bp.route("/run-status", methods=["GET"])
def get_run_status():
    """Return persisted pipeline progress for one runtime run."""
    run_id = request.args.get("run_id")
    if not run_id:
        return err("Missing required query param: run_id", 400)

    with db_session() as session:
        run = repo.get_runtime_run(session, run_id)
        if run is None:
            return err(f"Run not found: run_id={run_id!r}", 404)
        status = repo.artifact_status_for_run(session, run)

    return jsonify({"run_id": run_id, **status}), 200


@artifacts_bp.route("/weeks", methods=["GET"])
def list_weeks():
    return jsonify({"weeks": list_all_weeks()}), 200


@artifacts_bp.route("/evidence-images", methods=["GET"])
def list_evidence_images():
    """Finviz PNGs on disk for a week stem (W30 or 2026-W30)."""
    raw_stem = request.args.get("stem") or request.args.get("week")
    stem, error = _normalize_week_stem(raw_stem)
    if error:
        return error
    assert stem is not None

    if not _EVIDENCE_DIR.is_dir():
        return jsonify({"stem": stem, "images": []}), 200

    images = []
    for path in sorted(_EVIDENCE_DIR.glob(f"finviz_*_{stem}.png")):
        if not _EVIDENCE_FILE_RE.fullmatch(path.name):
            continue
        images.append(
            {
                "name": path.name,
                "label": _evidence_image_label(path.name),
                "url": f"/artifacts/evidence-file/{path.name}",
            }
        )
    return jsonify({"stem": stem, "images": images}), 200


@artifacts_bp.route("/evidence-file/<path:filename>", methods=["GET"])
def get_evidence_file(filename: str):
    """Serve a single evidence PNG (basename only; finviz_*.png)."""
    name = Path(filename).name
    if name != filename or not _EVIDENCE_FILE_RE.fullmatch(name):
        return err("Invalid evidence filename", 400)
    path = _EVIDENCE_DIR / name
    if not path.is_file():
        return err(f"Evidence file not found: {name}", 404)
    return send_from_directory(_EVIDENCE_DIR, name)


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
    """Archive by ``stem``, or a runtime run by ``run_id``."""
    run_id = request.args.get("run_id")
    if run_id:
        with db_session() as session:
            row = repo.get_runtime_human_score(session, str(run_id))
            if row is None:
                return err(f"No human score for run_id={run_id!r}", 404)
            return jsonify(row.payload), 200

    raw_stem = request.args.get("stem") or request.args.get("week")
    stem, error = _normalize_week_stem(raw_stem)
    if error:
        return error
    if stem is None:
        return err("Missing required query param: run_id or stem (e.g. W25)", 400)
    try:
        payload = load_human_score(stem)
    except ValueError as exc:
        return err(str(exc), 400)
    if payload is None:
        return err(f"No human score archive for {stem}", 404)
    return jsonify(payload), 200


@artifacts_bp.route("/human-score", methods=["POST"])
def save_human_score():
    """Persist a human-score report on a runtime run (keyed by run_id)."""
    body = request.get_json(silent=True) or {}
    run_id = body.get("run_id")
    report = body.get("report")
    if not run_id or not isinstance(report, Mapping):
        return err("Body must include run_id and report", 400)

    with db_session() as session:
        run = repo.get_runtime_run(session, str(run_id))
        if run is None:
            return err(f"Unknown run_id={run_id!r}", 404)
        payload = dict(report)
        payload.pop("rawMarkdown", None)
        form = payload.get("form") or {}
        repo.upsert_human_score(
            session,
            run,
            payload,
            total=payload.get("total"),
            consensus=payload.get("consensus"),
            human_call=form.get("humanCall"),
            confidence=form.get("confidence"),
        )
    return jsonify({"ok": True, "run_id": run_id}), 200


@artifacts_bp.route("/final-prediction", methods=["GET"])
def get_final_prediction():
    """Return the locked prediction for the selected run's week."""
    run_id = request.args.get("run_id")
    if not run_id:
        return err("Missing required query param: run_id", 400)

    with db_session() as session:
        run = repo.get_runtime_run(session, str(run_id))
        if run is None:
            return err(f"Unknown run_id={run_id!r}", 404)

        owner = run
        row = repo.get_runtime_final_prediction(session, str(run_id))
        if row is None:
            stem = run.week_stem or week_stem(run.prediction_date)
            owner = repo.get_runtime_run_with_final_prediction_for_week(session, stem)
            if owner is not None and owner.run_id is not None:
                row = repo.get_runtime_final_prediction(session, owner.run_id)

        if row is None:
            return err(f"No final prediction for run_id={run_id!r} or its week", 404)

        payload = dict(row.payload)
        if owner is not None and owner.run_id is not None:
            payload["runId"] = owner.run_id
        return jsonify(payload), 200


@artifacts_bp.route("/final-prediction", methods=["POST"])
def save_final_prediction():
    """Persist the final prediction on a runtime run (DB only"""
    body = request.get_json(silent=True) or {}
    run_id = body.get("run_id")
    report = body.get("report")
    if not run_id or not isinstance(report, Mapping):
        return err("Body must include run_id and report", 400)

    payload = dict(report)

    with db_session() as session:
        run = repo.get_runtime_run(session, str(run_id))
        if run is None:
            return err(f"Unknown run_id={run_id!r}", 404)
        stem = run.week_stem or week_stem(run.prediction_date)
        # One locked Team1 brief per week (delta reads a single file). Same run
        # may re-submit; a different run for the same week is rejected.
        owner = repo.get_runtime_run_with_final_prediction_for_week(session, stem)
        if owner is not None and owner.run_id != run.run_id:
            return err(
                f"Week {stem} already has a final prediction "
                f"from run_id={owner.run_id!r}",
                409,
            )
        repo.upsert_final_prediction(session, run, payload)

    return jsonify({"ok": True, "run_id": run_id}), 200


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
