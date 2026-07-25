import json as _json
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path

from flask import Blueprint, jsonify, request
from werkzeug.exceptions import BadRequest

from agents.delta.models import DeltaReport
from core.io import week_stem
from pipeline.config import LLMModelEntry
from pipeline.context import PipelineContext
from pipeline.stages import (
    run_almanac,
    run_delta,
    run_evidence,
    run_llm,
    run_macro,
    run_technical,
)
from server.config import load_server_config
from server.db import repository as repo
from server.db.context import db_session
from server.db.rehydrate import (
    almanac_from_payload,
    evidence_from_payload,
    macro_from_payload,
    technical_from_payload,
)
from server.utils import err, parse_date, require_fields

stages_bp = Blueprint("stages", __name__, url_prefix="/stages")

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "server.toml"

CONFIG = load_server_config(DEFAULT_CONFIG)

# Map each model slug accepted by /stages/llm to its configuration.
# Sourced from server.toml's [llm].models, keyed by slug.
_MODEL_REGISTRY: dict[str, LLMModelEntry] = {m.slug: m for m in CONFIG.llm.models}


def _jsonable(data: dict) -> dict:
    """Normalize a payload dict (dates/enums) to JSON-safe primitives."""
    return _json.loads(_json.dumps(data, default=str))


def _store_agent_output(
    prediction_date: date,
    run_id: str,
    horizon_days: int | None,
    agent_type: str,
    payload: dict,
) -> None:
    """Persist one agent output to the DB, creating/attaching its run."""
    stem = week_stem(prediction_date)
    with db_session() as session:
        run = repo.get_or_create_runtime_run(
            session,
            run_id=run_id,
            prediction_date=prediction_date,
            horizon_days=horizon_days,
            week_stem=stem,
        )
        repo.upsert_agent_output(session, run, agent_type, _jsonable(payload))


@stages_bp.route("/models", methods=["GET"])
def list_models():
    """Models currently enabled in server.toml — frontend should use this list."""
    return jsonify(
        {
            "models": [
                {
                    "key": m.slug,
                    "name": m.label,
                    "id": m.id,
                    "provider": m.provider,
                }
                for m in CONFIG.llm.models
            ]
        }
    ), 200


@stages_bp.route("/almanac", methods=["POST"])
def post_almanac():
    body = request.get_json(force=True) or {}
    try:
        require_fields(body, "prediction_date", "run_id", "horizon_days")
        prediction_date = parse_date(body["prediction_date"])
        run_id = str(body["run_id"])
        horizon_days = int(body["horizon_days"])
        if horizon_days <= 0:
            raise ValueError("horizon_days must be a positive integer")
    except (BadRequest, KeyError) as e:
        return err(str(e), 400)
    except (ValueError, TypeError) as e:
        return err(str(e), 400)

    ctx = PipelineContext(prediction_date=prediction_date)
    try:
        run_almanac(ctx, CONFIG)  # type: ignore[reportArgumentType]
    except Exception as e:
        return err(str(e), 500)
    assert ctx.almanac is not None

    output_dict = asdict(ctx.almanac)
    output_dict["horizon_days"] = horizon_days
    try:
        _store_agent_output(prediction_date, run_id, horizon_days, "almanac", output_dict)
    except ValueError as e:
        return err(str(e), 409)
    return jsonify(_jsonable(output_dict)), 200


@stages_bp.route("/technical", methods=["POST"])
def post_technical():
    body = request.get_json(force=True) or {}
    try:
        require_fields(body, "prediction_date", "run_id", "horizon_days")
        prediction_date = parse_date(body["prediction_date"])
        run_id = str(body["run_id"])
        horizon_days = int(body["horizon_days"])
        if horizon_days <= 0:
            raise ValueError("horizon_days must be a positive integer")
    except (BadRequest, KeyError) as e:
        return err(str(e), 400)
    except (ValueError, TypeError) as e:
        return err(str(e), 400)

    ctx = PipelineContext(prediction_date=prediction_date)
    try:
        run_technical(ctx, CONFIG)  # type: ignore[reportArgumentType]
    except Exception as e:
        return err(str(e), 500)
    assert ctx.technical is not None

    output_dict = asdict(ctx.technical)
    output_dict["horizon_days"] = horizon_days
    try:
        _store_agent_output(prediction_date, run_id, horizon_days, "technical", output_dict)
    except ValueError as e:
        return err(str(e), 409)
    return jsonify(_jsonable(output_dict)), 200


@stages_bp.route("/macro", methods=["POST"])
def post_macro():
    body = request.get_json(force=True) or {}
    try:
        require_fields(body, "prediction_date", "run_id", "horizon_days")
        prediction_date = parse_date(body["prediction_date"])
        run_id = str(body["run_id"])
        horizon_days = int(body["horizon_days"])
        if horizon_days <= 0:
            raise ValueError("horizon_days must be a positive integer")
    except (BadRequest, KeyError) as e:
        return err(str(e), 400)
    except (ValueError, TypeError) as e:
        return err(str(e), 400)

    ctx = PipelineContext(prediction_date=prediction_date)
    try:
        run_macro(ctx, CONFIG)  # type: ignore[reportArgumentType]
    except Exception as e:
        return err(str(e), 500)
    assert ctx.macro is not None

    output_dict = asdict(ctx.macro)
    output_dict["horizon_days"] = horizon_days
    try:
        _store_agent_output(prediction_date, run_id, horizon_days, "macro", output_dict)
    except ValueError as e:
        return err(str(e), 409)
    return jsonify(_jsonable(output_dict)), 200


@stages_bp.route("/evidence", methods=["POST"])
def post_evidence():
    body = request.get_json(force=True) or {}
    try:
        require_fields(body, "prediction_date", "run_id")
        prediction_date = parse_date(body["prediction_date"])
        run_id = str(body["run_id"])
    except (BadRequest, KeyError) as e:
        return err(str(e), 400)
    except ValueError as e:
        return err(str(e), 400)

    ctx = PipelineContext(prediction_date=prediction_date)
    try:
        run_evidence(ctx, CONFIG)  # type: ignore[reportArgumentType]
    except Exception as e:
        return err(str(e), 500)
    assert ctx.evidence is not None

    output_dict = asdict(ctx.evidence)
    output_dict["generated_at"] = datetime.now(timezone.utc).isoformat()
    try:
        _store_agent_output(prediction_date, run_id, None, "evidence", output_dict)
    except ValueError as e:
        return err(str(e), 409)
    return jsonify(_jsonable(output_dict)), 200


@stages_bp.route("/delta", methods=["POST"])
def post_delta():
    """Score the previous locked week against completed current-week data."""
    body = request.get_json(force=True) or {}
    try:
        require_fields(body, "prediction_date", "run_id")
        prediction_date = parse_date(body["prediction_date"])
        run_id = str(body["run_id"])
    except (BadRequest, KeyError) as exc:
        return err(str(exc), 400)
    except (ValueError, TypeError) as exc:
        return err(str(exc), 400)

    with db_session() as session:
        evidence = repo.get_agent_payload(session, run_id, "evidence")
    if evidence is None:
        return err(f"Evidence artifact not found for run_id={run_id!r}", 404)
    try:
        actuals_markdown = str(evidence["content"])
        generated_at = _artifact_generated_at(evidence)
    except (KeyError, TypeError, ValueError) as exc:
        return err(f"Invalid Evidence artifact: {exc}", 500)

    ctx = PipelineContext(prediction_date=prediction_date)
    try:
        run_delta(  # type: ignore[reportArgumentType]
            ctx,
            CONFIG,
            actuals_markdown=actuals_markdown,
            now=generated_at,
        )
    except FileNotFoundError as exc:
        return err(str(exc), 404)
    except ValueError as exc:
        return err(str(exc), 400)
    except Exception as exc:
        return err(str(exc), 500)

    assert ctx.delta is not None
    output = _jsonable(asdict(ctx.delta))
    with db_session() as session:
        run = repo.get_runtime_run(session, run_id)
        repo.add_delta_report(
            session,
            run,
            prediction_week=output.get("prediction_week"),
            schema_version=output.get("schema_version"),
            payload=output,
        )
    return jsonify(output), 200


def _artifact_generated_at(data: dict) -> datetime:
    value = data.get("generated_at")
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return datetime.now(timezone.utc)


@stages_bp.route("/llm", methods=["POST"])
def post_llm():
    body = request.get_json(force=True) or {}
    try:
        require_fields(body, "prediction_date", "run_id", "model", "horizon_days")
        prediction_date = parse_date(body["prediction_date"])
        run_id = str(body["run_id"])
        model_key = str(body["model"])
        horizon_days = int(body["horizon_days"])
        if horizon_days <= 0:
            raise ValueError("horizon_days must be a positive integer")
    except (BadRequest, KeyError) as e:
        return err(str(e), 400)
    except (ValueError, TypeError) as e:
        return err(str(e), 400)

    if model_key not in _MODEL_REGISTRY:
        return err(
            f"Unknown model '{model_key}'. Known models: {list(_MODEL_REGISTRY)}", 400
        )

    # All 4 required agent artifacts must exist for this run.
    with db_session() as session:
        payloads = {
            agent_type: repo.get_agent_payload(session, run_id, agent_type)
            for agent_type in ("almanac", "technical", "macro", "evidence")
        }

    almanac_data = payloads["almanac"]
    technical_data = payloads["technical"]
    macro_data = payloads["macro"]
    evidence_data = payloads["evidence"]
    if (
        almanac_data is None
        or technical_data is None
        or macro_data is None
        or evidence_data is None
    ):
        missing = [agent_type for agent_type, p in payloads.items() if p is None]
        return err(
            f"Missing agent artifacts for run_id={run_id!r}: {', '.join(missing)}",
            404,
        )

    # Load agent outputs into PipelineContext
    ctx = PipelineContext(prediction_date=prediction_date)
    try:
        ctx.almanac = almanac_from_payload(almanac_data)
        ctx.technical = technical_from_payload(technical_data)
        ctx.macro = macro_from_payload(macro_data)
        ctx.evidence = evidence_from_payload(evidence_data)

        with db_session() as session:
            delta_row = repo.get_latest_delta(session)
        if delta_row is not None:
            ctx.delta = DeltaReport.from_dict(delta_row.payload)

    except Exception as e:
        return err(f"Failed to load agent artifacts: {e}", 500)

    try:
        _slug, _row = run_llm(ctx, CONFIG, _MODEL_REGISTRY[model_key])  # type: ignore[reportArgumentType]
    except Exception as e:
        return jsonify(
            {
                "status": "failed",
                "model": model_key,
                "error": str(e),
            }
        ), 503

    llm_output = ctx.llm_outputs[-1]
    output_dict = asdict(llm_output)
    output_dict["horizon_days"] = horizon_days
    stem = week_stem(prediction_date)
    with db_session() as session:
        run = repo.get_or_create_runtime_run(
            session,
            run_id=run_id,
            prediction_date=prediction_date,
            horizon_days=horizon_days,
            week_stem=stem,
        )
        repo.upsert_llm_output(session, run, model_key, _jsonable(output_dict))
    return jsonify(_jsonable(output_dict)), 200


def _human_total(scores: dict) -> int:
    keys = ("macro", "technical", "almanac", "aiAgreement", "wildCard")
    return sum(int(scores.get(k) or 0) for k in keys)


@stages_bp.route("/human", methods=["POST"])
def post_human():
    """Persist the team human-score report for a run into the DB.

    Stage 5 (the human report) is submitted from the frontend. Storing it here
    makes it real backend data — so it is served on archive reads and can be
    exported to ``data/human/human_score_<stem>.md`` like every other artifact.
    """
    body = request.get_json(force=True) or {}
    try:
        require_fields(body, "prediction_date", "run_id", "form")
        prediction_date = parse_date(body["prediction_date"])
        run_id = str(body["run_id"])
        form = body["form"]
        if not isinstance(form, dict):
            raise ValueError("form must be an object")
        horizon_days = body.get("horizon_days")
        if horizon_days is not None:
            horizon_days = int(horizon_days)
            if horizon_days <= 0:
                raise ValueError("horizon_days must be a positive integer")
    except (BadRequest, KeyError) as e:
        return err(str(e), 400)
    except (ValueError, TypeError) as e:
        return err(str(e), 400)

    stem = week_stem(prediction_date)
    scores = form.get("scores") or {}
    total = body.get("total")
    if total is None:
        total = _human_total(scores)
    consensus = body.get("consensus") or "—"
    ai_said = body.get("aiSaid") if isinstance(body.get("aiSaid"), dict) else {}

    payload = _jsonable(
        {
            "form": form,
            "week": body.get("week") or stem,
            "predictionDate": prediction_date.isoformat(),
            "consensus": consensus,
            "aiSaid": ai_said,
            "total": total,
            "source": "run",
        }
    )

    with db_session() as session:
        run = repo.get_or_create_runtime_run(
            session,
            run_id=run_id,
            prediction_date=prediction_date,
            horizon_days=horizon_days,
            week_stem=stem,
        )
        repo.upsert_human_score(
            session,
            run,
            payload,
            total=total,
            consensus=consensus,
            human_call=form.get("humanCall"),
            confidence=form.get("confidence"),
        )
    return jsonify({"ok": True, "run_id": run_id, "week": stem, "total": total}), 200
