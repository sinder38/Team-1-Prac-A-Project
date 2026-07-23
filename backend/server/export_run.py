"""Export a selected run from data/outputs JSON into data/{agent} markdown.

Reads via artifact_path so a later sqlite swap only needs to change the loader.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from agents.almanac.almanac_agent import AlmanacAgent
from agents.io import week_stem
from agents.macro.macro_agent import MacroAgent
from agents.paths import DATA_DIR
from agents.schemas import (
    AlmanacOutput,
    Bias,
    CalendarEvent,
    CommodityData,
    Confidence,
    InstrumentTechnical,
    LLMOutput,
    MacroBias,
    MacroOutput,
    PredictedRange,
    Regime,
    SectorSignal,
    TechnicalOutput,
)
from server.files import write_markdown
from server.utils import OUTPUTS_ROOT, artifact_path, load_artifact


def export_run_to_data(
    prediction_date: date,
    run_id: str,
    horizon_days: int,
    *,
    outputs_root: Path | None = None,
    data_root: Path | None = None,
) -> list[str]:
    """Write archive-style markdown for whatever artifacts exist. Skip missing.

    One slot per week: paths are data/{agent}/*_{stem}.* (no run id), matching
    the existing archive layout. Exporting another run for the same week overwrites.
    """
    root = outputs_root or OUTPUTS_ROOT
    data = data_root or DATA_DIR
    stem = week_stem(prediction_date)

    # If this week has no files for the run, discover the stem from the run_id
    # (UI date can drift from the week the artifacts were written under).
    if not _run_has_artifacts(root, stem, run_id):
        discovered = _discover_stem_for_run(root, run_id)
        if discovered:
            stem = discovered

    written: list[str] = []

    def _try_load(agent_type: str, **kwargs) -> dict[str, Any] | None:
        path = _resolve_artifact(
            root if outputs_root is not None else None,
            agent_type,
            stem,
            run_id,
            horizon_days=kwargs.get("horizon_days"),
        )
        if path is None or not path.exists():
            return None
        try:
            return load_artifact(path)
        except (OSError, json.JSONDecodeError, FileNotFoundError):
            return None

    almanac_data = _try_load("almanac", horizon_days=horizon_days)
    if almanac_data is not None:
        output = _almanac_from_dict(almanac_data)
        path = write_markdown(
            data / "almanac" / f"almanac_agent_{stem}.md",
            AlmanacAgent().render_md(output, prediction_date),
        )
        written.append(_rel(path, data))

    technical_data = _try_load("technical", horizon_days=horizon_days)
    if technical_data is not None:
        output = _technical_from_dict(technical_data)
        path = write_markdown(
            data / "technical" / f"technical_agent_{stem}.md",
            _render_technical_md(output, prediction_date),
        )
        written.append(_rel(path, data))

    macro_data = _try_load("macro", horizon_days=horizon_days)
    if macro_data is not None:
        output = _macro_from_dict(macro_data)
        path = write_markdown(
            data / "macro" / f"macro_agent_{stem}.md",
            MacroAgent().render_md(output, prediction_date),
        )
        written.append(_rel(path, data))

    evidence_data = _try_load("evidence")
    if evidence_data is not None:
        content = str(evidence_data.get("content") or "")
        path = write_markdown(data / "evidence" / f"actuals_{stem}.md", content)
        written.append(_rel(path, data))

    # Prefer requested horizon; fall back to whatever llm files exist for this run.
    llm_items = _iter_llm_artifacts(root, stem, run_id, horizon_days)
    if not llm_items:
        llm_items = _iter_llm_artifacts(root, stem, run_id, horizon_days=None)

    for model_key, llm_data in llm_items:
        output = _llm_from_dict(llm_data)
        slug = _slug(model_key)
        path = write_markdown(
            data / "llm" / f"synthesis_{slug}_{stem}.txt",
            _render_llm_md(output, prediction_date),
        )
        written.append(_rel(path, data))

    return written


def _resolve_artifact(
    outputs_root: Path | None,
    agent_type: str,
    stem: str,
    run_id: str,
    *,
    horizon_days: int | None = None,
) -> Path | None:
    """Exact path first, then any matching horizon for this stem+run."""
    root = outputs_root or OUTPUTS_ROOT
    if outputs_root is None and horizon_days is not None and agent_type != "evidence":
        path = artifact_path(
            agent_type, stem, run_id, horizon_days=horizon_days
        )
        if path.exists():
            return path
    elif horizon_days is not None or agent_type == "evidence":
        path = _artifact_under(
            root, agent_type, stem, run_id, horizon_days=horizon_days
        )
        if path.exists():
            return path

    folder = root / agent_type
    if not folder.exists():
        return None
    if agent_type == "evidence":
        candidate = folder / f"evidence_{stem}_{run_id}.json"
        return candidate if candidate.exists() else None
    matches = sorted(folder.glob(f"{agent_type}_{stem}_{run_id}_*d.json"))
    return matches[0] if matches else None


def _run_has_artifacts(root: Path, stem: str, run_id: str) -> bool:
    if not root.exists():
        return False
    for folder in root.iterdir():
        if not folder.is_dir():
            continue
        if any(folder.glob(f"*_{stem}_{run_id}.json")) or any(
            folder.glob(f"*_{stem}_{run_id}_*.json")
        ):
            return True
        # llm_MODEL_Wxx_run_Nd.json
        if any(folder.glob(f"*_{stem}_{run_id}_*d.json")):
            return True
    return False


def _discover_stem_for_run(root: Path, run_id: str) -> str | None:
    """Find Wxx from any outputs filename that contains this run_id."""
    if not root.exists():
        return None
    patterns = (
        re.compile(rf"_(W\d{{2}})_{re.escape(run_id)}(?:_\d+d)?\.json$"),
        re.compile(rf"^llm_.+_(W\d{{2}})_{re.escape(run_id)}_\d+d\.json$"),
    )
    for path in root.rglob("*.json"):
        name = path.name
        for pattern in patterns:
            match = pattern.search(name)
            if match:
                return match.group(1)
    return None


def _render_technical_md(output: TechnicalOutput, prediction_date: date) -> str:
    """Compact MD from saved JSON (full agent render needs live OHLC frames)."""
    lines = [
        f"Technical Agent Output — Week of {prediction_date.day} "
        f"{prediction_date.strftime('%B %Y')}",
        "",
    ]
    for symbol, inst in output.instruments.items():
        lines.extend(
            [
                f"INSTRUMENT: {symbol}",
                f"LAST CLOSE: {inst.last_close}",
                f"EMA (8/21): {inst.ema_8} / {inst.ema_21}",
                f"Support / Resistance: {inst.key_support} - {inst.key_resistance}",
                f"TECHNICAL BIAS: {inst.trend_bias.value}.",
                f"CONFIDENCE: {inst.confidence.value}.",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _render_llm_md(output: LLMOutput, prediction_date: date) -> str:
    lines = [
        f"# LLM Agent Output — {output.model_name} — Week of {prediction_date}",
        "",
        f"1. Weekly Regime: {output.weekly_regime.value}",
        f"2. Confidence Score: {output.confidence.value}",
        "3. Key Supporting Evidence:",
        *[f"   - {e}" for e in output.supporting_evidence],
        "4. Key Contradictions:",
        *[f"   - {c}" for c in output.contradictions],
        f"5. Invalidation Conditions: {output.invalidation}",
        f"6. Predicted % move — SPX: {output.spx_range.low}% to {output.spx_range.high}%",
        f"   Predicted % move — NDX: {output.ndx_range.low}% to {output.ndx_range.high}%",
        f"   Predicted % move — IWM: {output.iwm_range.low}% to {output.iwm_range.high}%",
        f"7. Plain-English brief: {output.plain_english}",
        "8. Disclaimer: This is not financial advice.",
    ]
    return "\n".join(lines)


def _artifact_under(
    root: Path,
    agent_type: str,
    stem: str,
    run_id: str,
    *,
    horizon_days: int | None = None,
    model: str | None = None,
) -> Path:
    if agent_type == "llm":
        filename = f"llm_{model}_{stem}_{run_id}_{horizon_days}d.json"
    elif agent_type == "evidence":
        filename = f"evidence_{stem}_{run_id}.json"
    else:
        filename = f"{agent_type}_{stem}_{run_id}_{horizon_days}d.json"
    return root / agent_type / filename


def _iter_llm_artifacts(
    root: Path,
    stem: str,
    run_id: str,
    horizon_days: int | None,
) -> list[tuple[str, dict[str, Any]]]:
    llm_dir = root / "llm"
    if not llm_dir.exists():
        return []
    if horizon_days is None:
        paths = sorted(llm_dir.glob(f"llm_*_{stem}_{run_id}_*d.json"))
        pattern = re.compile(
            rf"^llm_(.+)_{re.escape(stem)}_{re.escape(run_id)}_\d+d\.json$"
        )
    else:
        paths = sorted(
            llm_dir.glob(f"llm_*_{stem}_{run_id}_{horizon_days}d.json")
        )
        pattern = re.compile(
            rf"^llm_(.+)_{re.escape(stem)}_{re.escape(run_id)}_{horizon_days}d\.json$"
        )
    found: list[tuple[str, dict[str, Any]]] = []
    for path in paths:
        match = pattern.match(path.name)
        if not match:
            continue
        try:
            found.append((match.group(1), json.loads(path.read_text(encoding="utf-8"))))
        except (OSError, json.JSONDecodeError):
            continue
    return found


def _slug(model_key: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", model_key).strip("_").lower() or "model"


def _rel(path: Path, data_root: Path) -> str:
    # Prefer paths like data/almanac/... relative to the repo root.
    root = data_root.parent if data_root.name == "data" else data_root
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _almanac_from_dict(data: dict[str, Any]) -> AlmanacOutput:
    return AlmanacOutput(
        prediction_date=date.fromisoformat(data["prediction_date"]),
        monthly_bias=Bias(data["monthly_bias"]),
        seasonal_bias=Bias(data["seasonal_bias"]),
        confidence=Confidence(data["confidence"]),
        thesis=data["thesis"],
        weekly_pattern=data.get("weekly_pattern", ""),
        sector_signals=[
            SectorSignal(
                sector=s["sector"], bias=Bias(s["bias"]), window=s["window"]
            )
            for s in data.get("sector_signals", [])
        ],
    )


def _technical_from_dict(data: dict[str, Any]) -> TechnicalOutput:
    return TechnicalOutput(
        prediction_date=date.fromisoformat(data["prediction_date"]),
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
            for k, v in data.get("instruments", {}).items()
        },
    )


def _macro_from_dict(data: dict[str, Any]) -> MacroOutput:
    return MacroOutput(
        prediction_date=date.fromisoformat(data["prediction_date"]),
        fed_rate=data["fed_rate"],
        yield_2y=data["yield_2y"],
        yield_10y=data["yield_10y"],
        yield_30y=data["yield_30y"],
        dxy=CommodityData(**data["dxy"]),
        wti_oil=CommodityData(**data["wti_oil"]),
        gold=CommodityData(**data["gold"]),
        macro_bias=MacroBias(data["macro_bias"]),
        primary_driver=data["primary_driver"],
        confidence=Confidence(data["confidence"]),
        invalidation=data["invalidation"],
        next_fomc_date=(
            date.fromisoformat(data["next_fomc_date"])
            if data.get("next_fomc_date")
            else None
        ),
        hold_probability=data.get("hold_probability", 0.0),
        cut_probability=data.get("cut_probability", 0.0),
        fomc_direction=data.get("fomc_direction", "N/A"),
        yield_curve=data.get("yield_curve", "N/A"),
        yield_10y_direction=data.get("yield_10y_direction", "N/A"),
        week_ahead_calendar=[
            CalendarEvent(**e) for e in data.get("week_ahead_calendar", [])
        ],
        key_earnings=data.get("key_earnings", []),
        confirmed_news=data.get("confirmed_news", []),
    )


def _llm_from_dict(data: dict[str, Any]) -> LLMOutput:
    return LLMOutput(
        prediction_date=date.fromisoformat(data["prediction_date"]),
        model_name=data.get("model_name") or data.get("model") or "llm",
        weekly_regime=Regime(data["weekly_regime"]),
        confidence=Confidence(data["confidence"]),
        spx_range=PredictedRange(**data["spx_range"]),
        ndx_range=PredictedRange(**data["ndx_range"]),
        iwm_range=PredictedRange(**data["iwm_range"]),
        invalidation=data.get("invalidation", ""),
        plain_english=data.get("plain_english", ""),
        supporting_evidence=list(data.get("supporting_evidence") or []),
        contradictions=list(data.get("contradictions") or []),
    )
