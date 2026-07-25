"""Render stored JSON payloads back to Markdown.

Used by archive reads (the agent card ``rawData``) and the export endpoint.

Note (see migration decision): technical Markdown cannot be reproduced exactly
because the agent's own ``render_md`` depends on live market frames (Support 2 /
Resistance 2, bar date) that the schema does not store. Technical rendering here
is therefore intentionally lossy — it reproduces the fields the schema carries.
"""

from __future__ import annotations

import re
from datetime import date
from types import SimpleNamespace

from agents.almanac.almanac_agent import AlmanacAgent
from agents.llm.base_llm import BaseLLMAgent
from agents.macro.macro_agent import MacroAgent
from agents.schemas import TechnicalOutput
from server.db import rehydrate

_LABELS = {
    "SPX": "S&P 500 (SPX), Daily Chart",
    "NDX": "Nasdaq 100 (NDX), Daily Chart",
    "IWM": "Russell 2000 (IWM), Daily Chart",
}


def _pred_date(payload: dict) -> date:
    return date.fromisoformat(str(payload["prediction_date"])[:10])


def render_markdown(agent_type: str, payload: dict) -> str:
    if agent_type == "almanac":
        return AlmanacAgent().render_md(
            rehydrate.almanac_from_payload(payload), _pred_date(payload)
        )
    if agent_type == "macro":
        # Bypass __init__ so no data-source clients are constructed; render_md
        # and its helpers are stateless (staticmethods over the output).
        agent = MacroAgent.__new__(MacroAgent)
        return agent.render_md(rehydrate.macro_from_payload(payload), _pred_date(payload))
    if agent_type == "evidence":
        return str(payload.get("content", ""))
    if agent_type == "technical":
        return _render_technical(rehydrate.technical_from_payload(payload), _pred_date(payload))
    raise ValueError(f"Cannot render markdown for agent_type={agent_type!r}")


class _SynthesisRenderer(BaseLLMAgent):
    """Minimal agent used only to reuse ``BaseLLMAgent.render_md`` for a stored
    ``LLMOutput``. ``query`` is never called during rendering."""

    agent_type = "llm"

    def __init__(self, model_name: str):
        self.model_name = model_name

    def query(self, prompt: str) -> str:  # pragma: no cover - never invoked
        raise NotImplementedError("render-only agent")


def render_llm_synthesis(payload: dict) -> str:
    """Reproduce a per-model ``synthesis_<slug>_<stem>.txt`` from stored JSON.

    Lossless: this is the agent's own ``render_md`` over the parsed output.
    """
    output = rehydrate.llm_from_payload(payload)
    return _SynthesisRenderer(output.model_name).render_md(output, output.prediction_date)


# _row() keys expected by build_comparison_md, mapped from the parsed comparison
# payload's per-model fields (server.archive._comparison_model).
_COMPARISON_FIELD_MAP = {
    "regime": "consensus",
    "confidence": "confidenceLabel",
    "spx": "spx",
    "ndx": "ndx",
    "iwm": "iwm",
    "evidence": "evidence",
    "contradiction": "contradiction",
    "invalidation": "invalidation",
    "plain_english": "plainEnglish",
}


def render_llm_comparison_from_outputs(
    outputs: list[tuple[str, dict]], stem: str, prediction_date: date
) -> str:
    """Rebuild ``llm_comparison_<stem>.md`` from per-model LLMOutput payloads.

    ``outputs`` is a list of ``(model_slug, payload)``. This reuses the pipeline's
    own ``build_comparison_md`` / ``_row`` so live-run exports match the original
    generator exactly.
    """
    from agents.llm.multi_model_runner import _row, build_comparison_md

    rows_by_slug: dict[str, dict] = {}
    models = []
    for slug, payload in outputs:
        output = rehydrate.llm_from_payload(payload)
        rows_by_slug[slug] = _row(output)
        models.append(SimpleNamespace(slug=slug, label=output.model_name))
    return build_comparison_md(rows_by_slug, models, stem, prediction_date)


def render_llm_comparison_from_payload(
    payload: dict, stem: str, prediction_date: date
) -> str:
    """Rebuild ``llm_comparison_<stem>.md`` from a parsed comparison payload.

    Fallback for archive weeks, which store only the parsed comparison (no
    per-model outputs). Lossy relative to the original: only the fields the
    parser captured are reproduced.
    """
    from agents.llm.multi_model_runner import build_comparison_md

    rows_by_slug: dict[str, dict] = {}
    models = []
    for model in payload.get("models", []):
        name = str(model.get("name", "—"))
        rows_by_slug[name] = {
            row_key: model.get(src_key, "—")
            for row_key, src_key in _COMPARISON_FIELD_MAP.items()
        }
        models.append(SimpleNamespace(slug=name, label=name))
    return build_comparison_md(rows_by_slug, models, stem, prediction_date)


# Human-score dimensions in report order: (payload key, table label, short label).
# Adapted from feat/hsr-json-provider (server/human_score.py).
_HUMAN_DIMENSIONS = [
    ("macro", "Macro / News Weight", "Macro"),
    ("technical", "Technical Structure", "Technical"),
    ("almanac", "Almanac Seasonal Weight", "Almanac"),
    ("aiAgreement", "AI Model Agreement Quality", "AI Agreement"),
    ("wildCard", "Wild Card / Human Observation", "Wild Card"),
]

_HUMAN_EVIDENCE_BULLETS = [
    ("almanac", "R3 Almanac Agent Output"),
    ("macro", "R4 Macro Agent Output"),
    ("technical", "R5 Technical Agent Output"),
    ("llm", "R6 LLM Comparison Output"),
]

_HUMAN_PLACEHOLDER = "________"


def _signed(value) -> str:
    try:
        n = int(value)
    except (TypeError, ValueError):
        n = 0
    return f"+{n}" if n > 0 else str(n)


def _human_total(scores: dict) -> int:
    return sum(int(scores.get(key) or 0) for key, _, _ in _HUMAN_DIMENSIONS)


def _week_title(payload: dict) -> str:
    # ``week`` may be "W25" or "2026-W25"; the report header wants "Week 25".
    m = re.search(r"W(\d{1,2})", str(payload.get("week", "")), re.I)
    return f"Week {int(m.group(1))}" if m else str(payload.get("week") or "—")


def render_human_score(payload: dict) -> str:
    """Rebuild ``human_score_<stem>.md`` from the stored human-score payload.

    W28-style markdown (AI consensus, score table, five-dimension judgement,
    call/confidence, override/wild-card/invalidation, evidence). Adapted from
    feat/hsr-json-provider's ``render_human_score_markdown`` to read the DB
    payload directly. Lossy: the five-dimension judgement reuses each
    dimension's table reasoning (the original long-form prose is not stored).
    """
    form = payload.get("form") or {}
    scores = form.get("scores") or {}
    reasoning = form.get("reasoning") or {}
    evidence = form.get("evidence") or {}
    ai_said = payload.get("aiSaid") or {}
    consensus = (payload.get("consensus") or "—").strip()

    total = payload.get("total")
    if total is None:
        total = _human_total(scores)

    table = [
        "| Dimension                         | AI Said                                   | Team Score | Team Reasoning |",
        "| --------------------------------- | ----------------------------------------- | :--------: | -------------- |",
    ]
    for key, label, _ in _HUMAN_DIMENSIONS:
        said = str(ai_said.get(key) or "—").replace("|", "/")
        reason = str(reasoning.get(key) or _HUMAN_PLACEHOLDER).replace("|", "/")
        table.append(f"| **{label}** | {said} | **{_signed(scores.get(key))}** | {reason} |")

    judgements = []
    for i, (key, label, _) in enumerate(_HUMAN_DIMENSIONS, 1):
        judgements.append(
            f"### {i}. {label} — Score: {_signed(scores.get(key))}\n\n"
            f"{reasoning.get(key) or _HUMAN_PLACEHOLDER}\n"
        )

    breakdown = " + ".join(
        f"{short} {_signed(scores.get(key))}" for key, _, short in _HUMAN_DIMENSIONS
    )
    evidence_lines = [f"* {label}" for key, label in _HUMAN_EVIDENCE_BULLETS if evidence.get(key)]

    parts = [
        f"# Human Score Analyst Output — {_week_title(payload)}",
        "",
        "## AI Consensus",
        "",
        f"**{consensus}**",
        "",
        "---",
        "",
        "## Human Score Table",
        "",
        *table,
        "",
        "---",
        "",
        "## Human Score Total",
        "",
        f"**{_signed(total)}**",
        "",
        f"({breakdown})",
        "",
        "---",
        "",
        "## Five-Dimension Judgement",
        "",
        *judgements,
        "---",
        "",
        "## Human Call",
        "",
        f"**{form.get('humanCall') or 'Neutral'}**",
        "",
        "---",
        "",
        "## Confidence",
        "",
        f"**{form.get('confidence') or 'Medium'}**",
        "",
        "---",
        "",
        "## Override Paragraph",
        "",
        form.get("overrideParagraph") or _HUMAN_PLACEHOLDER,
        "",
        "---",
        "",
        "## Wild Card Insight",
        "",
        form.get("wildCardInsight") or _HUMAN_PLACEHOLDER,
        "",
        "---",
        "",
        "## Invalidation Condition",
        "",
        form.get("invalidation") or _HUMAN_PLACEHOLDER,
        "",
        "---",
        "",
        "## Evidence Used",
        "",
        *evidence_lines,
    ]
    return "\n".join(parts).rstrip() + "\n"


def _render_technical(output: TechnicalOutput, prediction_date: date) -> str:
    """Lossy technical report from schema fields only (no frame-derived data)."""
    parts = [
        f"Technical Agent Output — Week of {prediction_date.day} "
        f"{prediction_date.strftime('%B %Y')}",
        "",
    ]
    for symbol, inst in output.instruments.items():
        parts += [
            "---",
            "",
            f"INSTRUMENT: {_LABELS.get(symbol, symbol)}",
            f"LAST CLOSE: {inst.last_close}",
            "",
            "8 EMA vs PRICE:",
            f" - Price is {'ABOVE' if inst.last_close > inst.ema_8 else 'BELOW'} the 8 EMA.",
            f" - 8 EMA at ~{inst.ema_8}.",
            "",
            "8 EMA vs 21 EMA:",
            f" - 8 EMA is {'ABOVE' if inst.ema_8 > inst.ema_21 else 'BELOW'} 21 EMA.",
            f" - 21 EMA at ~{inst.ema_21}.",
            f" - EMA condition: {inst.trend_bias.value}.",
            "",
            "KEY LEVELS:",
            f" - Resistance 1: {inst.key_resistance}.",
            f" - Support 1: {inst.key_support}.",
            "",
            f"TECHNICAL BIAS: {inst.trend_bias.value}.",
            f"CONFIDENCE: {inst.confidence.value}.",
            "",
        ]
    return "\n".join(parts).rstrip() + "\n"
