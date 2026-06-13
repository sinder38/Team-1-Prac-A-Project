import json
from abc import ABC, abstractmethod
from dataclasses import asdict
from datetime import date
from typing import Generic, TypeVar, Union

from agents.schemas import AlmanacOutput, LLMOutput, MacroOutput, TechnicalOutput

AgentOutput = Union[TechnicalOutput, AlmanacOutput, MacroOutput, LLMOutput]

T = TypeVar("T", TechnicalOutput, AlmanacOutput, MacroOutput, LLMOutput)


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
