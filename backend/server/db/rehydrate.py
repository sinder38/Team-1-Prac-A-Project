"""Rebuild typed agent dataclasses from stored JSON payloads.

The DB stores each agent output as ``asdict(output)``. These helpers turn a
stored payload back into its dataclass so it can be fed to a PipelineContext or
re-rendered to Markdown via the agent's ``render_md``.
"""

from __future__ import annotations

from datetime import date

from core.schemas import (
    AlmanacOutput,
    Bias,
    CalendarEvent,
    CommodityData,
    Confidence,
    EvidenceOutput,
    InstrumentTechnical,
    LLMOutput,
    MacroBias,
    MacroOutput,
    PredictedRange,
    Regime,
    SectorSignal,
    TechnicalOutput,
)


def _as_date(value: object) -> date:
    return date.fromisoformat(str(value)[:10])


def almanac_from_payload(data: dict) -> AlmanacOutput:
    return AlmanacOutput(
        prediction_date=_as_date(data["prediction_date"]),
        monthly_bias=Bias(data["monthly_bias"]),
        seasonal_bias=Bias(data["seasonal_bias"]),
        confidence=Confidence(data["confidence"]),
        thesis=data["thesis"],
        weekly_pattern=data.get("weekly_pattern", ""),
        sector_signals=[
            SectorSignal(sector=s["sector"], bias=Bias(s["bias"]), window=s["window"])
            for s in data.get("sector_signals", [])
        ],
    )


def technical_from_payload(data: dict) -> TechnicalOutput:
    return TechnicalOutput(
        prediction_date=_as_date(data["prediction_date"]),
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


def macro_from_payload(data: dict) -> MacroOutput:
    return MacroOutput(
        prediction_date=_as_date(data["prediction_date"]),
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
            _as_date(data["next_fomc_date"]) if data.get("next_fomc_date") else None
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


def evidence_from_payload(data: dict) -> EvidenceOutput:
    return EvidenceOutput(
        prediction_date=_as_date(data["prediction_date"]),
        week=data["week"],
        content=data["content"],
    )


def llm_from_payload(data: dict) -> LLMOutput:
    return LLMOutput(
        prediction_date=_as_date(data["prediction_date"]),
        model_name=data["model_name"],
        weekly_regime=Regime(data["weekly_regime"]),
        confidence=Confidence(data["confidence"]),
        spx_range=PredictedRange(**data["spx_range"]),
        ndx_range=PredictedRange(**data["ndx_range"]),
        iwm_range=PredictedRange(**data["iwm_range"]),
        invalidation=data["invalidation"],
        plain_english=data["plain_english"],
        supporting_evidence=data.get("supporting_evidence", []),
        contradictions=data.get("contradictions", []),
    )
