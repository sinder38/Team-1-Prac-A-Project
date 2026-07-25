from dataclasses import dataclass, field
from datetime import date

from agents.delta.models import DeltaReport
from agents.schemas import (
    AlmanacOutput,
    EvidenceOutput,
    LLMOutput,
    MacroOutput,
    TechnicalOutput,
)


@dataclass
class PipelineContext:
    prediction_date: date
    horizon_days: int = 7
    almanac: AlmanacOutput | None = None
    technical: TechnicalOutput | None = None
    macro: MacroOutput | None = None
    evidence: EvidenceOutput | None = None
    delta: DeltaReport | None = None
    llm_outputs: list[LLMOutput] = field(default_factory=list)
