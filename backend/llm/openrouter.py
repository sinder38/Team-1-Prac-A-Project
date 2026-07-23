"""
Sprint 4: Multi-LLM Synthesis Pipeline
Role: LLM Agent Implementor / Synthesis (R8).

CONTRACT: we own ONLY query() on the BaseLLMAgent subclass. We do NOT modify any
other base_llm method (build_prompt / parse_response / run / render_md).

Failure policy:
  - Config errors (missing key / missing upstream inputs) -> abort LOUDLY before any model runs.
  - Per-model runtime errors (API / parse) -> caught, marked FAILED in the table, and the
    process exits non-zero at the end so CI turns red. No silent dummy data anywhere.
"""

import os
import sys
import time
import json
from datetime import date
from pathlib import Path

# === Absolute path injection ===
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from openai import OpenAI  # type: ignore
from dotenv import load_dotenv, find_dotenv  # type: ignore

from llm.base import BaseLLMAgent
from llm.comparison import _row, build_comparison_md
from core.io import FileSaver
from pipeline.config import LLMModelEntry, load_config

# === Load environment variables ===
load_dotenv(find_dotenv())
load_dotenv(dotenv_path=BASE_DIR / ".env")

REPO_ROOT = BASE_DIR.parent
INPUTS_DIR = REPO_ROOT / "data" / "outputs"            # where the data agents write their JSON
OUTPUTS_LLM_DIR = REPO_ROOT / "data" / "outputs" / "llm"
HUMAN_LLM_DIR = REPO_ROOT / "data" / "llm"

DEFAULT_CONFIG = BASE_DIR / "pipeline.toml"

def _get_retry_delay(attempt: int) -> int:
    """Get delay time in seconds inbetween LLM API requests"""
    return 10 + 2**attempt


def iso_tag(d: date) -> str:
    """Machine/pipeline week tag, e.g. '2026-W25' (isocalendar). MUST match what the
    data agents write to data/outputs/ and what base_llm.build_prompt reads."""
    w = d.isocalendar()
    return f"{w.year}-W{w.week:02d}"


def human_tag(d: date) -> str:
    """Human-facing week tag, e.g. 'W24' (Python %W). Matches the team's existing
    synthesis_*_WXX / llm_comparison_WXX files (= ISO week - 1 in 2026)."""
    return f"W{d.strftime('%W')}"


def _cell(text) -> str:
    """Make a string safe inside a single Markdown table cell."""
    return (str(text) if text else "—").replace("|", "/").replace("\n", " ").replace("\r", " ").strip() or "—"


def _serialize(output) -> str:
    """Serialize an LLMOutput to schema-valid JSON via the model's own serializer."""
    if hasattr(output, "model_dump_json"):          # pydantic v2
        return output.model_dump_json(indent=2)
    if hasattr(output, "json"):                      # pydantic v1
        return output.json(indent=2)
    import dataclasses
    if dataclasses.is_dataclass(output) and not isinstance(output, type):
        return json.dumps(dataclasses.asdict(output), indent=2, default=str)
    raise TypeError("Cannot serialize LLMOutput.")



class OpenRouterAgent(BaseLLMAgent):
    def __init__(self, model_name: str, model_id: str, max_retries = 3):
        self.model_name = model_name
        self.model_id = model_id
        self.max_retries = max_retries

        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:  # defensive; the real gate is the pre-flight check in __main__
            raise RuntimeError(f"FATAL: OPENROUTER_API_KEY missing. Cannot initialize {self.model_name}.")

        self.client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key, timeout=45.0)

    def query(self, prompt: str) -> str:
        """Send prompt to OpenRouter. Retry on failure; raise if all retries are exhausted.
        Does NO parsing or sanitization — that is base_llm's responsibility."""
        system_instruction = (
            "You are a strict financial data formatter. "
            "You MUST output exactly the requested keys in PLAIN TEXT format, separated by colons. "
            "DO NOT OUTPUT JSON FORMAT. "
            "For index ranges, you MUST strictly use the word 'to' (e.g., -1.5 to 2.0). "
            "Do NOT wrap your response in markdown code blocks."
        )

        for attempt in range(self.max_retries):
            try:
                print(f"[{self.model_name}] OpenRouter request (attempt {attempt + 1}/{self.max_retries})...")
                response = self.client.chat.completions.create(
                    model=self.model_id,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                )

                # Explicit guard: empty choices or None content -> retry / loud fail,
                # never hand None to base_llm (which would AttributeError on .strip()).
                if not response.choices or not response.choices[0].message.content:
                    raise RuntimeError(f"[{self.model_name}] Empty response from provider.")

                return response.choices[0].message.content

            except Exception as e:
                print(f"[{self.model_name}] API call failed: {e}", file=sys.stderr)
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"[{self.model_name}] Exhausted all {self.max_retries} API retries.") from e
                time.sleep(_get_retry_delay(attempt))

        return ""  # unreachable (loop always returns or raises); kept for type-checkers


if __name__ == "__main__":
    prediction_date = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    iso_t = iso_tag(prediction_date)
    human_t = human_tag(prediction_date)

    print(f"\n🚀 Multi-LLM pipeline | run {prediction_date} | machine={iso_t} | human={human_t}\n")

    # =====================================================================
    # PRE-FLIGHT 1 — Config: missing key is a setup error, not a model failure.
    # Abort before the loop so it can't degrade into four "FAILED" rows.
    # =====================================================================
    if not os.getenv("OPENROUTER_API_KEY"):
        raise SystemExit("❌ ABORT: OPENROUTER_API_KEY is not set. Add it to your .env and retry.")

    config = load_config(DEFAULT_CONFIG)

    # =====================================================================
    # PRE-FLIGHT 2 — Inputs: refuse to run if upstream agents haven't delivered.
    # Prevents the models from fabricating on an empty context.
    # NOTE: this is only meaningful once the Dev Lead fixes the base_llm root path
    # (parents[3]); until then base_llm reads backend/data/outputs and this green
    # light does NOT guarantee the models actually receive the context.
    # =====================================================================
    missing = [
        INPUTS_DIR / t / f"{iso_t}.json"
        for t in ("technical", "almanac", "macro")
        if not (INPUTS_DIR / t / f"{iso_t}.json").exists()
    ]
    if missing:
        raise SystemExit(
            f"❌ ABORT: Missing upstream agent outputs for {iso_t}:\n  "
            + "\n  ".join(str(p) for p in missing)
            + "\n\nRun the Technical/Almanac/Macro agents first (or ping R3/R4/R5)."
        )
    print(f"✅ Pre-flight passed: key present, all upstream {iso_t} inputs found.\n")

    rows_by_slug = {}

    for entry in config.llm.models:
        print("====================================")
        print(f"🤖 {entry.label}  ({entry.id})")

        try:
            agent = OpenRouterAgent(model_name=entry.label, model_id=entry.id)
            output = agent.run(prediction_date)

            FileSaver(OUTPUTS_LLM_DIR / entry.slug).save(_serialize(output), f"{iso_t}.json")
            FileSaver(HUMAN_LLM_DIR).save(agent.render_md(output, prediction_date), f"synthesis_{entry.slug}_{human_t}.txt")

            rows_by_slug[entry.slug] = _row(output)
            print(f"✅ {entry.label}: outputs saved.")

        except Exception as e:
            print(f"❌ {entry.label} failed: {type(e).__name__} - {e}", file=sys.stderr)
            sys.exit(1)

    # Always write the comparison table; failed columns are explicitly marked FAILED.
    FileSaver(HUMAN_LLM_DIR).save(
        build_comparison_md(rows_by_slug, config.llm.models, human_t, prediction_date),
        f"llm_comparison_{human_t}.md",
    )
    print(f"\n📊 Wrote data/llm/llm_comparison_{human_t}.md")

    print("🏁 Done.")
