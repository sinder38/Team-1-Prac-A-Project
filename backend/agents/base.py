import json
from abc import ABC, abstractmethod
from dataclasses import asdict
from datetime import date
from pathlib import Path
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

    def save_json(self, output: T, prediction_date: date) -> None:
        """Serialize output to data/outputs/{agent_type}/{YYYY-WNN}.json"""
        week = prediction_date.isocalendar()
        filename = f"{week.year}-W{week.week:02d}.json"
        out_dir = Path(__file__).parent.parent / "data" / "outputs" / self.agent_type
        out_dir.mkdir(parents=True, exist_ok=True)
        with open(out_dir / filename, "w", encoding="utf-8") as f:
            json.dump(asdict(output), f, indent=2, default=str)

    @abstractmethod
    def save_md(self, output: T, prediction_date: date) -> None:
        """
        Render output into MD format.
        Each subclass implements its own template logic.
        """
        ...

    def export(self, output: T, prediction_date: date, fmt: str = "json") -> None:
        """Calls save_json or save_md based on fmt argument."""
        if fmt == "json":
            self.save_json(output, prediction_date)
        elif fmt == "md":
            self.save_md(output, prediction_date)
        else:
            raise ValueError(f"Unknown format: {fmt!r}. Expected 'json' or 'md'.")
