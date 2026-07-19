import json as _json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from flask import Blueprint, jsonify, request
from werkzeug.exceptions import BadRequest

from agents.db import (
    save_agent_artifact,
    load_agent_artifact,
    agent_artifact_exists,
    save_llm_artifact,
    ingest_human_score_md,
)
from agents.io import week_stem
from agents.pipeline.config import (
    ArtifactsConfig,
    LLMConfig,
    LLMModelEntry,
    PipelineConfig,
    PipelineSection,
    StagesConfig,
)
from agents.pipeline.context import PipelineContext
from agents.pipeline.stages import (
    run_almanac,
    run_evidence,
    run_llm,
    run_macro,
    run_technical,
)
from agents.schemas import (
    AlmanacOutput,
    Bias,
    CalendarEvent,
    CommodityData,
    Confidence,
    EvidenceOutput,
    InstrumentTechnical,
    MacroBias,
    MacroOutput,
    SectorSignal,
    TechnicalOutput,
)
from server.config import load_server_config
from server.utils import err, parse_date, require_fields

stages_bp = Blueprint("stages", __name__, url_prefix="/stages")

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "server.toml"

CONFIG = load_server_config(DEFAULT_CONFIG)

# Map each model slug accepted by /stages/llm to its configuration.
# Sourced from server.toml's [llm].models, keyed by slug.
_MODEL_REGISTRY: dict[str, LLMModelEntry] = {m.slug: m for m in CONFIG.llm.models}


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
        run_almanac(ctx, CONFIG)
    except Exception as e:
        return err(str(e), 500)
    assert ctx.almanac is not None

    stem = week_stem(prediction_date)

    output_dict = asdict(ctx.almanac)
    output_dict["horizon_days"] = horizon_days
    save_agent_artifact(
        agent_type="almanac",
        week_stem=stem,
        run_id=run_id,
        horizon_days=horizon_days,
        data=output_dict,
        prediction_date=prediction_date,
    )
    output_dict = _json.loads(_json.dumps(output_dict, default=str))
    return jsonify(output_dict), 200


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
        run_technical(ctx, CONFIG)
    except Exception as e:
        return err(str(e), 500)
    assert ctx.technical is not None

    stem = week_stem(prediction_date)
    output_dict = asdict(ctx.technical)
    output_dict["horizon_days"] = horizon_days
    save_agent_artifact(
        agent_type="technical",
        week_stem=stem,
        run_id=run_id,
        horizon_days=horizon_days,
        data=output_dict,
        prediction_date=prediction_date,
    )
    output_dict = _json.loads(_json.dumps(output_dict, default=str))
    return jsonify(output_dict), 200


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
        run_macro(ctx, CONFIG)
    except Exception as e:
        return err(str(e), 500)
    assert ctx.macro is not None

    stem = week_stem(prediction_date)
    output_dict = asdict(ctx.macro)
    output_dict["horizon_days"] = horizon_days
    save_agent_artifact(
        agent_type="macro",
        week_stem=stem,
        run_id=run_id,
        horizon_days=horizon_days,
        data=output_dict,
        prediction_date=prediction_date,
    )
    output_dict = _json.loads(_json.dumps(output_dict, default=str))
    return jsonify(output_dict), 200


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
        run_evidence(ctx, CONFIG)
    except Exception as e:
        return err(str(e), 500)
    assert ctx.evidence is not None

    stem = week_stem(prediction_date)
    output_dict = asdict(ctx.evidence)
    save_agent_artifact(
        agent_type="evidence",
        week_stem=stem,
        run_id=run_id,
        data=output_dict,
        prediction_date=prediction_date,
    )
    output_dict = _json.loads(_json.dumps(output_dict, default=str))
    return jsonify(output_dict), 200


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

    stem = week_stem(prediction_date)

    # Check all 4 required agent artifacts exist
    missing = []
    for agent_type in ("almanac", "technical", "macro", "evidence"):
        exists = (
            agent_artifact_exists(agent_type=agent_type, week_stem=stem, run_id=run_id)
            if agent_type == "evidence"
            else agent_artifact_exists(
                agent_type=agent_type,
                week_stem=stem,
                run_id=run_id,
                horizon_days=horizon_days,
            )
        )
        if not exists:
            missing.append(agent_type)

    if missing:
        return err(
            f"Missing agent artifacts for run_id={run_id!r}: {', '.join(missing)}",
            404,
        )

    # Load agent outputs from db
    ctx = PipelineContext(prediction_date=prediction_date)
    try:

        almanac_data = load_agent_artifact(
            agent_type="almanac", week_stem=stem, run_id=run_id, horizon_days=horizon_days
        )

        technical_data = load_agent_artifact(
            agent_type="technical", week_stem=stem, run_id=run_id, horizon_days=horizon_days
        )

        macro_data = load_agent_artifact(
            agent_type="macro", week_stem=stem, run_id=run_id, horizon_days=horizon_days
        )

        evidence_data = load_agent_artifact(
            agent_type="evidence", week_stem=stem, run_id=run_id
        )

        ctx.almanac = AlmanacOutput(
            prediction_date=date.fromisoformat(almanac_data["prediction_date"]),
            monthly_bias=Bias(almanac_data["monthly_bias"]),
            seasonal_bias=Bias(almanac_data["seasonal_bias"]),
            confidence=Confidence(almanac_data["confidence"]),
            thesis=almanac_data["thesis"],
            weekly_pattern=almanac_data.get("weekly_pattern", ""),
            sector_signals=[
                SectorSignal(
                    sector=s["sector"], bias=Bias(s["bias"]), window=s["window"]
                )
                for s in almanac_data.get("sector_signals", [])
            ],
        )

        ctx.technical = TechnicalOutput(
            prediction_date=date.fromisoformat(technical_data["prediction_date"]),
            instruments={
                k: InstrumentTechnical(
                    last_close=v["last_close"],
                    ema_8=v["ema_8"],
                    ema_21=v["ema_21"],
                    trend_bias=Bias(v["trend_bias"]),
                    key_support=v["key_support"],
                    key_resistance=v["key_resistance"],
                    confidence=Confidence(v["confidence"]),
                )
                for k, v in technical_data.get("instruments", {}).items()
            },
        )

        ctx.macro = MacroOutput(
            prediction_date=date.fromisoformat(macro_data["prediction_date"]),
            fed_rate=macro_data["fed_rate"],
            yield_2y=macro_data["yield_2y"],
            yield_10y=macro_data["yield_10y"],
            yield_30y=macro_data["yield_30y"],
            dxy=CommodityData(**macro_data["dxy"]),
            wti_oil=CommodityData(**macro_data["wti_oil"]),
            gold=CommodityData(**macro_data["gold"]),
            macro_bias=MacroBias(macro_data["macro_bias"]),
            primary_driver=macro_data["primary_driver"],
            confidence=Confidence(macro_data["confidence"]),
            invalidation=macro_data["invalidation"],
            next_fomc_date=(
                date.fromisoformat(macro_data["next_fomc_date"])
                if macro_data.get("next_fomc_date")
                else None
            ),
            hold_probability=macro_data.get("hold_probability", 0.0),
            cut_probability=macro_data.get("cut_probability", 0.0),
            fomc_direction=macro_data.get("fomc_direction", "N/A"),
            yield_curve=macro_data.get("yield_curve", "N/A"),
            yield_10y_direction=macro_data.get("yield_10y_direction", "N/A"),
            week_ahead_calendar=[
                CalendarEvent(**e) for e in macro_data.get("week_ahead_calendar", [])
            ],
            key_earnings=macro_data.get("key_earnings", []),
            confirmed_news=macro_data.get("confirmed_news", []),
        )

        ctx.evidence = EvidenceOutput(
            prediction_date=date.fromisoformat(evidence_data["prediction_date"]),
            week=evidence_data["week"],
            content=evidence_data["content"],
        )

    except Exception as e:
        return err(f"Failed to load agent artifacts: {e}", 500)

    try:
        _slug, _row = run_llm(ctx, CONFIG, _MODEL_REGISTRY[model_key])
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
    save_llm_artifact(
        week_stem=stem,
        run_id=run_id,
        horizon_days=horizon_days,
        model=model_key,
        data=output_dict,
        prediction_date=prediction_date,
    )
    return jsonify(output_dict), 200


@stages_bp.route("/human-score", methods=["POST"])
def post_human_score():
    """
    Late step: agents + LLM already in DB.
    Scans data/human/human_score_{Wxx}.md and stores into human.db.
    If the .md is not uploaded yet → 404 and skip.
    """
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

    stem = week_stem(prediction_date)

    # Preconditions: prior stages already done (no re-run)
    missing = []
    for agent_type in ("almanac", "technical", "macro", "evidence"):
        exists = (
            agent_artifact_exists(agent_type=agent_type, week_stem=stem, run_id=run_id)
            if agent_type == "evidence"
            else agent_artifact_exists(
                agent_type=agent_type,
                week_stem=stem,
                run_id=run_id,
                horizon_days=horizon_days,
            )
        )
        if not exists:
            missing.append(agent_type)

    if missing:
        return err(
            f"Run agents first. Missing for run_id={run_id!r}: {', '.join(missing)}",
            404,
        )

    # At least one LLM row for this week/run/horizon
    try:
        with __import__("agents.db", fromlist=["get_llm_conn"]).get_llm_conn() as conn:
            row = conn.execute(
                """
                SELECT 1 FROM llm_outputs
                WHERE week_stem = ? AND run_id = ? AND horizon_days = ?
                LIMIT 1
                """,
                (stem, run_id, horizon_days),
            ).fetchone()
    except Exception as e:
        return err(str(e), 500)

    if row is None:
        return err(f"Run LLM first. No llm_outputs for {stem}/{run_id} horizon={horizon_days}", 404)

    if not ingest_human_score_md(stem):
        return err(
            f"human_score_{stem}.md not uploaded yet — skipped. "
            f"Add data/human/human_score_{stem}.md then POST again.",
            404,
        )

    return jsonify({"week": stem, "run_id": run_id, "stored": True}), 200