from __future__ import annotations

from abc import abstractmethod
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING
import json
import re
import sys

from agents.base import BaseAgent
from agents.schemas import LLMOutput, PredictedRange, Regime, Confidence

if TYPE_CHECKING:
    from agents.pipeline.context import PipelineContext


class BaseLLMAgent(BaseAgent):
    agent_type = "llm"
    model_name: str  # e.g. "claude", "deepseek-local" — must be set by subclass

    @abstractmethod
    def query(self, prompt: str) -> str:
        """Send prompt to the LLM, return raw text response."""
        ...

    def build_prompt(self, prediction_date: date, ctx: PipelineContext | None = None) -> str:
        """
        Assemble a structured prompt from the in-memory PipelineContext.
        Falls back to reading data/outputs/ JSON files if no context is provided
        (preserves compatibility with multi_model_runner.__main__ standalone mode).
        """
        from dataclasses import asdict
        from agents.pipeline.context import PipelineContext as _PC

        context_blocks = []

        if ctx is not None:
            # In-memory pipeline path: use PipelineContext directly
            for agent_type, output in [
                ("technical", ctx.technical),
                ("almanac", ctx.almanac),
                ("macro", ctx.macro),
                ("evidence", ctx.evidence),
            ]:
                if output is None:
                    continue
                if agent_type == "evidence":
                    context_blocks.append(f"=== EVIDENCE ===\n{output.content}")
                else:
                    data = asdict(output)
                    context_blocks.append(
                        f"=== {agent_type.upper()} AGENT ===\n{json.dumps(data, indent=2, default=str)}"
                    )
        else:
            # Standalone / legacy path: read JSON from data/outputs/
            outputs_dir = Path(__file__).resolve().parents[3] / "data" / "outputs"
            week = prediction_date.isocalendar()
            week_key = f"{week.year}-W{week.week:02d}.json"

            for agent_type in ("technical", "almanac", "macro"):
                agent_file = outputs_dir / agent_type / week_key
                if not agent_file.exists():
                    print(f"⚠️  Missing agent input: {agent_file}", file=sys.stderr)
                    continue
                try:
                    data = json.loads(agent_file.read_text(encoding="utf-8"))
                except json.JSONDecodeError as e:
                    raise ValueError(f"Malformed JSON in {agent_file}: {e}") from e
                context_blocks.append(f"=== {agent_type.upper()} AGENT ===\n{json.dumps(data, indent=2)}")

            if not context_blocks:
                week = prediction_date.isocalendar()
                week_key = f"{week.year}-W{week.week:02d}.json"
                outputs_dir = Path(__file__).resolve().parents[3] / "data" / "outputs"
                raise ValueError(
                    f"No agent inputs found for {week_key} under {outputs_dir}. "
                    "Run the Technical/Almanac/Macro agents first."
                )

        context = "\n\n".join(context_blocks) if context_blocks else "No agent data available."

        return (
            f"You are a market analyst. Based on the following data for the week of {prediction_date}, "
            f"provide a structured market prediction for SPX, NDX, and IWM.\n\n"
            f"{context}\n\n"
            f"Respond in this exact format:\n"
            f"WEEKLY_REGIME: [Bullish/Bearish/Neutral/Uncertain]\n"
            f"CONFIDENCE: [Low/Medium/High/Low-Medium]\n"
            f"SPX_RANGE: [low%] to [high%]\n"
            f"NDX_RANGE: [low%] to [high%]\n"
            f"IWM_RANGE: [low%] to [high%]\n"
            f"EVIDENCE_1: ...\n"
            f"EVIDENCE_2: ...\n"
            f"EVIDENCE_3: ...\n"
            f"CONTRADICTION_1: ...\n"
            f"CONTRADICTION_2: ...\n"
            f"INVALIDATION: ...\n"
            f"PLAIN_ENGLISH: ...\n"
            f"DISCLAIMER: This is not financial advice."
        )

    def parse_response(self, raw: str, prediction_date: date) -> LLMOutput:
        """
        Parse LLM raw text response into LLMOutput.
        Core fields (regime, confidence, ranges) are required — missing fields raise.
        Supplementary fields are optional.
        """
        lines = {
            line.split(":", 1)[0].strip(): line.split(":", 1)[1].strip()
            for line in raw.strip().splitlines()
            if ":" in line
        }

        def require(key: str) -> str:
            value = lines.get(key, "").strip()
            if not value:
                raise ValueError(f"Missing required field '{key}' in the LLM response.")
            return value

        def parse_range(field: str) -> PredictedRange:
            val = require(field)
            nums = re.findall(r"[-+]?\d*\.?\d+", val)
            if len(nums) >= 2:
                return PredictedRange(low=float(nums[0]), high=float(nums[1]))
            if len(nums) == 1:
                return PredictedRange(low=float(nums[0]), high=float(nums[0]))
            raise ValueError(f"Could not parse a numeric range for '{field}' from {val!r}.")

        return LLMOutput(
            model_name=self.model_name,
            prediction_date=prediction_date,
            weekly_regime=Regime(require("WEEKLY_REGIME")),
            confidence=Confidence(require("CONFIDENCE")),
            spx_range=parse_range("SPX_RANGE"),
            ndx_range=parse_range("NDX_RANGE"),
            iwm_range=parse_range("IWM_RANGE"),
            supporting_evidence=[
                lines[k] for k in ("EVIDENCE_1", "EVIDENCE_2", "EVIDENCE_3") if lines.get(k, "").strip()
            ],
            contradictions=[
                lines[k] for k in ("CONTRADICTION_1", "CONTRADICTION_2") if lines.get(k, "").strip()
            ],
            invalidation=lines.get("INVALIDATION", "").strip(),
            plain_english=lines.get("PLAIN_ENGLISH", "").strip(),
        )

    def run(self, prediction_date: date, **kwargs) -> LLMOutput:
        prompt = self.build_prompt(prediction_date, kwargs.get("ctx"))
        raw = self.query(prompt)
        return self.parse_response(raw, prediction_date)

    def render_md(self, output: LLMOutput, prediction_date: date) -> str:
        lines = [
            f"# LLM Agent Output — {self.model_name} — Week of {prediction_date}",
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
