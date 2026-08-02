import json
from abc import ABC, abstractmethod
from dataclasses import asdict
from datetime import date
from typing import Generic, TypeVar, Union

from core.schemas import AlmanacOutput, EvidenceOutput, LLMOutput, MacroOutput, TechnicalOutput

AgentOutput = Union[TechnicalOutput, AlmanacOutput, MacroOutput, LLMOutput, EvidenceOutput]

T = TypeVar("T", TechnicalOutput, AlmanacOutput, MacroOutput, LLMOutput, EvidenceOutput)


class BaseAgent(ABC, Generic[T]):
    agent_type: str  # must be set by subclass, e.g. "technical", "almanac"

    @abstractmethod
    def run(self, prediction_date: date, **kwargs) -> T:
        """
        Fetch, process, and return a typed output matching the agent's schema.
        Subclasses define their own additional parameters via **kwargs.
        """
        ...

    def render_json(self, output: T, prediction_date: date) -> str:
        """Return JSON string for output. Override to customize serialization."""
        return json.dumps(asdict(output), indent=2, default=str)

    @abstractmethod
    def render_md(self, output: T, prediction_date: date) -> str:
        """Return Markdown string for output. Subclasses implement their own template."""
        ...

    @classmethod
    def parse_md(cls, text: str, prediction_date: date | None = None) -> T:
        """Parse Markdown produced by ``render_md`` back into a typed output.

        The inverse of ``render_md``. The prediction date is read from the
        document when present; pass ``prediction_date`` to override or as a
        fallback for agents whose Markdown does not carry a recoverable date.

        Optional: agents whose Markdown cannot be reconstructed from the schema
        do not override this. Parsing may be lossy where the rendered document
        carries more than the schema stores.
        """
        raise NotImplementedError(f"{cls.__name__} does not support parse_md")
