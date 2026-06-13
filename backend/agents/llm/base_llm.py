from abc import abstractmethod
from datetime import date
from pathlib import Path
import json

from agents.base import BaseAgent
from agents.schemas import LLMOutput, PredictedRange, Regime, Confidence


class BaseLLMAgent(BaseAgent):
    agent_type = "llm"
    model_name: str  # e.g. "claude", "deepseek-local" — must be set by subclass

    @abstractmethod
    def query(self, prompt: str) -> str:
        """Send prompt to the LLM, return raw text response."""
        ...

    def build_prompt(self, prediction_date: date) -> str:
        """
        Load all data agent JSON outputs from data/outputs/ and assemble
        a structured prompt for the LLM.
        """
        outputs_dir = Path(__file__).parent.parent.parent / "data" / "outputs"
        week = prediction_date.isocalendar()
        week_key = f"{week.year}-W{week.week:02d}.json"

        context_blocks = []
        for agent_type in ("technical", "almanac", "macro"):
            agent_file = outputs_dir / agent_type / week_key
            if agent_file.exists():
                data = json.loads(agent_file.read_text(encoding="utf-8"))
                context_blocks.append(f"=== {agent_type.upper()} AGENT ===\n{json.dumps(data, indent=2)}")

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
        Subclasses may override if their LLM returns a different format.
        """
        lines = {
            line.split(":", 1)[0].strip(): line.split(":", 1)[1].strip()
            for line in raw.strip().splitlines()
            if ":" in line
        }

        def parse_range(val: str) -> PredictedRange:
            parts = val.replace("%", "").split("to")
            return PredictedRange(low=float(parts[0].strip()), high=float(parts[1].strip()))

        return LLMOutput(
            model_name=self.model_name,
            prediction_date=prediction_date,
            weekly_regime=Regime(lines.get("WEEKLY_REGIME", "Uncertain")),
            confidence=Confidence(lines.get("CONFIDENCE", "Low")),
            spx_range=parse_range(lines.get("SPX_RANGE", "0 to 0")),
            ndx_range=parse_range(lines.get("NDX_RANGE", "0 to 0")),
            iwm_range=parse_range(lines.get("IWM_RANGE", "0 to 0")),
            supporting_evidence=[
                lines[k] for k in ("EVIDENCE_1", "EVIDENCE_2", "EVIDENCE_3") if k in lines
            ],
            contradictions=[
                lines[k] for k in ("CONTRADICTION_1", "CONTRADICTION_2") if k in lines
            ],
            invalidation=lines.get("INVALIDATION", ""),
            plain_english=lines.get("PLAIN_ENGLISH", ""),
        )

    def run(self, prediction_date: date, **kwargs) -> LLMOutput:
        prompt = self.build_prompt(prediction_date)
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
