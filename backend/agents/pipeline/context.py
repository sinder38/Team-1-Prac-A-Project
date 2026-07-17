from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING

from agents.schemas import (
    AlmanacOutput,
    EvidenceOutput,
    LLMOutput,
    MacroOutput,
    TechnicalOutput,
)

if TYPE_CHECKING:
    from agents.delta.delta_engine import DeltaReport


@dataclass
class PipelineContext:
    prediction_date: date
    almanac: AlmanacOutput | None = None
    technical: TechnicalOutput | None = None
    macro: MacroOutput | None = None
    evidence: EvidenceOutput | None = None
    delta: DeltaReport | None = None
    llm_outputs: list[LLMOutput] = field(default_factory=list)
