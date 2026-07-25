"""Render stored JSON payloads back to Markdown.

Used by archive reads (the agent card ``rawData``) and the export endpoint.

Note (see migration decision): technical Markdown cannot be reproduced exactly
because the agent's own ``render_md`` depends on live market frames (Support 2 /
Resistance 2, bar date) that the schema does not store. Technical rendering here
is therefore intentionally lossy — it reproduces the fields the schema carries.
"""

from __future__ import annotations

from datetime import date

from agents.almanac.almanac_agent import AlmanacAgent
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
