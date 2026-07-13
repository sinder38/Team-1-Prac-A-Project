import json
import json as _json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from flask import Blueprint, jsonify, request
from werkzeug.exceptions import BadRequest

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
from server.utils import artifact_path, err, parse_date, require_fields

stages_bp = Blueprint("stages", __name__, url_prefix="/stages")
# TODO: move to config instead of manual
_NO_ARTIFACTS_CONFIG = PipelineConfig(
    pipeline=PipelineSection(prediction_date="auto"),
    stages=StagesConfig(),
    llm=LLMConfig(models=[], max_retries=5),
    artifacts=ArtifactsConfig(save_json=False, save_md=False),
)

# Registry maps short model keys (as accepted by the /stages/llm endpoint) → LLMModelEntry.
_MODEL_REGISTRY: dict[str, LLMModelEntry] = {
    "example": LLMModelEntry(id="example/example:free"),
    "nemotron": LLMModelEntry(id="nvidia/nemotron-3-super-120b-a12b:free"),
    "gptoss": LLMModelEntry(id="openai/gpt-oss-120b:free"),
    "gemma": LLMModelEntry(id="google/gemma-4-31b-it:free"),
    "laguna": LLMModelEntry(id="poolside/laguna-m.1:free"),
}


def _write_artifact(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


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
        run_almanac(ctx, _NO_ARTIFACTS_CONFIG)
    except Exception as e:
        return err(str(e), 500)

    stem = week_stem(prediction_date)
    output_dict = asdict(ctx.almanac)
    output_dict["horizon_days"] = horizon_days
    path = artifact_path("almanac", stem, run_id, horizon_days=horizon_days)
    _write_artifact(path, output_dict)
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
        run_technical(ctx, _NO_ARTIFACTS_CONFIG)
    except Exception as e:
        return err(str(e), 500)

    stem = week_stem(prediction_date)
    output_dict = asdict(ctx.technical)
    output_dict["horizon_days"] = horizon_days
    path = artifact_path("technical", stem, run_id, horizon_days=horizon_days)
    _write_artifact(path, output_dict)
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
        run_macro(ctx, _NO_ARTIFACTS_CONFIG)
    except Exception as e:
        return err(str(e), 500)

    stem = week_stem(prediction_date)
    output_dict = asdict(ctx.macro)
    output_dict["horizon_days"] = horizon_days
    path = artifact_path("macro", stem, run_id, horizon_days=horizon_days)
    _write_artifact(path, output_dict)
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
        run_evidence(ctx, _NO_ARTIFACTS_CONFIG)
    except Exception as e:
        return err(str(e), 500)

    stem = week_stem(prediction_date)
    output_dict = asdict(ctx.evidence)
    path = artifact_path("evidence", stem, run_id)
    _write_artifact(path, output_dict)
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
        if agent_type == "evidence":
            path = artifact_path(agent_type, stem, run_id)
        else:
            path = artifact_path(agent_type, stem, run_id, horizon_days=horizon_days)
        if not path.exists():
            missing.append(str(path))

    if missing:
        return err(
            f"Missing agent artifacts for run_id={run_id!r}: {', '.join(missing)}",
            404,
        )

    # Load agent outputs from disk into PipelineContext
    ctx = PipelineContext(prediction_date=prediction_date)
    try:

        def _load(agent_type, **kwargs):
            p = artifact_path(agent_type, stem, run_id, **kwargs)
            return json.loads(p.read_text(encoding="utf-8"))

        almanac_data = _load("almanac", horizon_days=horizon_days)
        technical_data = _load("technical", horizon_days=horizon_days)
        macro_data = _load("macro", horizon_days=horizon_days)
        evidence_data = _load("evidence")

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
        _slug, _row = run_llm(ctx, _NO_ARTIFACTS_CONFIG, _MODEL_REGISTRY[model_key])
    except Exception as e:
        return err(str(e), 500)

    llm_output = ctx.llm_outputs[-1]
    output_dict = asdict(llm_output)
    output_dict["horizon_days"] = horizon_days
    path = artifact_path(
        "llm", stem, run_id, model=model_key, horizon_days=horizon_days
    )
    _write_artifact(path, output_dict)
    output_dict = _json.loads(_json.dumps(output_dict, default=str))
    return jsonify(output_dict), 200
