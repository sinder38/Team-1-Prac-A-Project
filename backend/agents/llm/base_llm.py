from __future__ import annotations

import json
import re
import sys
from abc import abstractmethod
from datetime import date
from typing import TYPE_CHECKING

from agents.base import BaseAgent
from agents.paths import OUTPUTS_DIR
from agents.schemas import (
    Confidence,
    LLMOutput,
    PredictedRange,
    Regime,
)

if TYPE_CHECKING:
    from agents.pipeline.context import PipelineContext


class BaseLLMAgent(BaseAgent):
    agent_type = "llm"
    model_name: str  # Must be set by the subclass.

    @abstractmethod
    def query(self, prompt: str) -> str:
        """Send a prompt to the LLM and return the raw text response."""
        ...

    def build_prompt(
        self,
        prediction_date: date,
        ctx: PipelineContext | None = None,
    ) -> str:
        """
        Assemble a structured prompt from the in-memory PipelineContext.

        Falls back to reading data/outputs JSON files if no context is
        provided. This preserves compatibility with the standalone
        multi-model runner.
        """
        from dataclasses import asdict

        context_blocks: list[str] = []

        if ctx is not None:
            # In-memory pipeline path: use PipelineContext directly.
            for agent_type, output in [
                ("technical", ctx.technical),
                ("almanac", ctx.almanac),
                ("macro", ctx.macro),
                ("evidence", ctx.evidence),
                ("delta", ctx.delta),
            ]:
                if output is None:
                    continue

                if agent_type == "evidence":
                    context_blocks.append(
                        f"=== EVIDENCE ===\n{output.content}"
                    )
                else:
                    data = asdict(output)
                    context_blocks.append(
                        f"=== {agent_type.upper()} AGENT ===\n"
                        f"{json.dumps(data, indent=2, default=str)}"
                    )
        else:
            # Standalone or legacy path: read JSON from data/outputs.
            outputs_dir = OUTPUTS_DIR
            week = prediction_date.isocalendar()
            week_key = f"{week.year}-W{week.week:02d}.json"

            for agent_type in ("technical", "almanac", "macro"):
                agent_file = outputs_dir / agent_type / week_key

                if not agent_file.exists():
                    print(
                        f"⚠️  Missing agent input: {agent_file}",
                        file=sys.stderr,
                    )
                    continue

                try:
                    data = json.loads(
                        agent_file.read_text(encoding="utf-8")
                    )
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Malformed JSON in {agent_file}: {exc}"
                    ) from exc

                context_blocks.append(
                    f"=== {agent_type.upper()} AGENT ===\n"
                    f"{json.dumps(data, indent=2)}"
                )

            if not context_blocks:
                raise ValueError(
                    f"No agent inputs found for {week_key} under "
                    f"{OUTPUTS_DIR}. Run the Technical, Almanac, and "
                    "Macro agents first."
                )

        context = (
            "\n\n".join(context_blocks)
            if context_blocks
            else "No agent data available."
        )

        horizon_days = 7

        if ctx is not None:
            horizon_days = int(
                getattr(ctx, "horizon_days", 7) or 7
            )

        period = (
            f"the week of {prediction_date}"
            if horizon_days <= 7
            else (
                f"the next {horizon_days} days starting "
                f"{prediction_date}"
            )
        )

        return (
            f"You are a market analyst. Based on the following data for "
            f"{period}, provide a structured market prediction for SPX, "
            f"NDX, and IWM, covering that same {horizon_days}-day "
            f"horizon.\n\n"
            f"{context}\n\n"
            "Respond in this exact format:\n"
            "WEEKLY_REGIME: [Bullish/Bearish/Neutral/Uncertain]\n"
            "CONFIDENCE: [Low/Medium/High/Low-Medium]\n"
            "SPX_RANGE: [low%] to [high%]\n"
            "NDX_RANGE: [low%] to [high%]\n"
            "IWM_RANGE: [low%] to [high%]\n"
            "EVIDENCE_1: ...\n"
            "EVIDENCE_2: ...\n"
            "EVIDENCE_3: ...\n"
            "CONTRADICTION_1: ...\n"
            "CONTRADICTION_2: ...\n"
            "INVALIDATION: ...\n"
            "PLAIN_ENGLISH: ...\n"
            "DISCLAIMER: This is not financial advice."
        )

    def parse_response(
        self,
        raw: str,
        prediction_date: date,
    ) -> LLMOutput:
        """
        Parse the raw LLM response into an LLMOutput.

        Core fields are required. Supplementary evidence,
        contradictions, and explanation fields are optional.
        """
        lines = {
            line.split(":", 1)[0].strip():
            line.split(":", 1)[1].strip()
            for line in raw.strip().splitlines()
            if ":" in line
        }

        def require(key: str) -> str:
            value = lines.get(key, "").strip()

            if not value:
                raise ValueError(
                    f"Missing required field '{key}' "
                    "in the LLM response."
                )

            return value

        def parse_regime(field: str) -> Regime:
            value = require(field)

            try:
                return Regime(value.title())
            except ValueError:
                lowered = value.lower()

                if "bull" in lowered:
                    return Regime.BULLISH

                if "bear" in lowered:
                    return Regime.BEARISH

                if any(
                    word in lowered
                    for word in ("mixed", "range", "choppy")
                ):
                    return Regime.MIXED

                if any(
                    word in lowered
                    for word in ("neutral", "flat", "side")
                ):
                    return Regime.NEUTRAL

                return Regime.UNCERTAIN

        def parse_confidence(field: str) -> Confidence:
            value = require(field)

            try:
                return Confidence(value.title())
            except ValueError:
                lowered = value.lower()

                if "low" in lowered and "med" in lowered:
                    return Confidence.LOW_MEDIUM

                if "high" in lowered:
                    return Confidence.HIGH

                if "low" in lowered:
                    return Confidence.LOW

                return Confidence.MEDIUM

        def parse_range(field: str) -> PredictedRange:
            value = require(field)

            # Extract signed integers or decimals from the response.
            numbers = re.findall(r"[-+]?\d*\.?\d+", value)

            if len(numbers) >= 2:
                return PredictedRange(
                    low=float(numbers[0]),
                    high=float(numbers[1]),
                )

            if len(numbers) == 1:
                number = float(numbers[0])
                return PredictedRange(low=number, high=number)

            raise ValueError(
                f"Could not parse a numeric range for "
                f"'{field}' from {value!r}."
            )

        return LLMOutput(
            model_name=self.model_name,
            prediction_date=prediction_date,
            weekly_regime=parse_regime("WEEKLY_REGIME"),
            confidence=parse_confidence("CONFIDENCE"),
            spx_range=parse_range("SPX_RANGE"),
            ndx_range=parse_range("NDX_RANGE"),
            iwm_range=parse_range("IWM_RANGE"),
            supporting_evidence=[
                lines[key]
                for key in (
                    "EVIDENCE_1",
                    "EVIDENCE_2",
                    "EVIDENCE_3",
                )
                if lines.get(key, "").strip()
            ],
            contradictions=[
                lines[key]
                for key in (
                    "CONTRADICTION_1",
                    "CONTRADICTION_2",
                )
                if lines.get(key, "").strip()
            ],
            invalidation=lines.get("INVALIDATION", "").strip(),
            plain_english=lines.get("PLAIN_ENGLISH", "").strip(),
        )

    def run(
        self,
        prediction_date: date,
        **kwargs,
    ) -> LLMOutput:
        prompt = self.build_prompt(
            prediction_date,
            kwargs.get("ctx"),
        )
        raw = self.query(prompt)

        return self.parse_response(raw, prediction_date)

    def render_md(self, output: LLMOutput) -> str:
        """
        Render Markdown using the prediction date stored in the output.

        The date no longer needs to be passed as a separate argument.
        """
        prediction_date = output.prediction_date

        lines = [
            (
                f"# LLM Agent Output — {self.model_name} "
                f"— Week of {prediction_date}"
            ),
            "",
            f"1. Weekly Regime: {output.weekly_regime.value}",
            f"2. Confidence Score: {output.confidence.value}",
            "3. Key Supporting Evidence:",
            *[
                f"   - {evidence}"
                for evidence in output.supporting_evidence
            ],
            "4. Key Contradictions:",
            *[
                f"   - {contradiction}"
                for contradiction in output.contradictions
            ],
            (
                "5. Invalidation Conditions: "
                f"{output.invalidation}"
            ),
            (
                "6. Predicted % move — SPX: "
                f"{output.spx_range.low}% to "
                f"{output.spx_range.high}%"
            ),
            (
                "   Predicted % move — NDX: "
                f"{output.ndx_range.low}% to "
                f"{output.ndx_range.high}%"
            ),
            (
                "   Predicted % move — IWM: "
                f"{output.iwm_range.low}% to "
                f"{output.iwm_range.high}%"
            ),
            (
                "7. Plain-English brief: "
                f"{output.plain_english}"
            ),
            "8. Disclaimer: This is not financial advice.",
        ]

        return "\n".join(lines)
