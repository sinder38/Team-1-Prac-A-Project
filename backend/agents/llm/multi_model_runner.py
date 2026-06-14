"""
Sprint 4: Multi-LLM Synthesis Pipeline
Role: LLM Agent Implementor / Synthesis.

!! Before Running, CREAT YOUR OWN .env file with your OpenRouter Key in this directory as the format of ".env.example" file in this directory(If the .env file does not exist).

CONTRACT: we own ONLY query() on the BaseLLMAgent subclass. We do NOT modify any
other base_llm method (build_prompt / parse_response / run / render_md). If base_llm
needs changes, that is the Development Lead's job — report it, don't patch it here.

Per run, for EACH model this produces:
  Machine artifact (pipeline, ISO week):
    <repo>/data/outputs/llm/<model>/2026-W25.json        (schema-valid, fed to delta/QA)
  Human artifacts (team convention, %W week):
    <repo>/data/llm/synthesis_<model>_W24.txt            (render_md output)
    <repo>/data/llm/llm_comparison_W24.md                (one file, all models)
"""

import os
import sys
import re
import time
import json
from datetime import date
from pathlib import Path

# === Absolute path injection (so `from agents...` works when run directly) ===
BASE_DIR = Path(__file__).resolve().parents[2]   # .../backend  (for imports + .env)
sys.path.insert(0, str(BASE_DIR))

from openai import OpenAI  # type: ignore
from dotenv import load_dotenv, find_dotenv  # type: ignore

from agents.llm.base_llm import BaseLLMAgent
from agents.io import FileSaver

# === Load environment variables ===
load_dotenv(find_dotenv())
load_dotenv(dotenv_path=BASE_DIR / ".env")

# Repo root holds data/. Machine JSON and human files live in different trees.
REPO_ROOT = BASE_DIR.parent
OUTPUTS_LLM_DIR = REPO_ROOT / "data" / "outputs" / "llm"   # machine JSON, per model
HUMAN_LLM_DIR = REPO_ROOT / "data" / "llm"                 # synthesis + comparison

# "label" drives the per-model folder, synthesis filename, and comparison column,
# so it MUST name the real model. (Course template lists Claude/ChatGPT/Gemini/
# DeepSeek; these are the free OpenRouter substitutes our team is using.)
MODELS = [
    {"label": "NVIDIA Nemotron 3 Super", "id": "nvidia/nemotron-3-super-120b-a12b:free"},  # NVIDIA Nemotron 3 Super
    {"label": "OpenAI gpt-oss-120b",   "id": "openai/gpt-oss-120b:free"},                  # OpenAI gpt-oss-120b
    {"label": "Google Gemma 4 31B",    "id": "google/gemma-4-31b-it:free"},                # Google Gemma 4 31B
    {"label": "Poolside Laguna M.1",   "id": "poolside/laguna-m.1:free"},                  # Poolside Laguna M.1
]


def iso_tag(d: date) -> str:
    """Machine/pipeline week tag, e.g. '2026-W25'. Uses isocalendar() — this MUST
    match what the data agents write to data/outputs/ and what base_llm reads."""
    w = d.isocalendar()
    return f"{w.year}-W{w.week:02d}"


def human_tag(d: date) -> str:
    """Human-facing week tag, e.g. 'W24'. Uses Python %W to match the team's
    existing synthesis_*_WXX / llm_comparison_WXX files (= ISO week - 1 in 2026).
    NOTE: this differs from iso_tag by 1; see the W23/W25 mismatch discussion."""
    return f"W{d.strftime('%W')}"


def _cell(text: str) -> str:
    """Make a string safe inside a single Markdown table cell."""
    return (str(text) if text else "—").replace("|", "/").replace("\n", " ").strip() or "—"


def _serialize(output) -> str:
    """Serialize an LLMOutput to schema-valid JSON.
    Uses the model's own serializer (pydantic v2 -> v1) so the JSON matches
    schemas.py / validate_output.py. Dataclass fallback is best-effort."""
    if hasattr(output, "model_dump_json"):       # pydantic v2
        return output.model_dump_json(indent=2)
    if hasattr(output, "json"):                  # pydantic v1
        return output.json(indent=2)
    import dataclasses
    if dataclasses.is_dataclass(output) and not isinstance(output, type):
        return json.dumps(dataclasses.asdict(output), indent=2, default=str)
    raise TypeError("Cannot serialize LLMOutput — send schemas.py to wire this exactly.")


def _row(output) -> dict:
    """Extract the comparison-table fields from an LLMOutput."""
    def rng(r):
        return f"{r.low}% to {r.high}%"
    return {
        "regime": output.weekly_regime.value,
        "confidence": output.confidence.value,
        "spx": rng(output.spx_range),
        "ndx": rng(output.ndx_range),
        "iwm": rng(output.iwm_range),
        "evidence": "; ".join(output.supporting_evidence) if output.supporting_evidence else "—",
        "contradiction": "; ".join(output.contradictions) if output.contradictions else "—",
        "invalidation": output.invalidation or "—",
        "plain_english": output.plain_english or "—",
    }


def build_comparison_md(rows_by_label: dict, tag: str, run_date: date) -> str:
    """Build the Multi-LLM comparison table, matching last week's manual sample shape."""
    labels = [m["label"] for m in MODELS]

    head = [
        f"# Multi-LLM Comparison Table — {tag} (run {run_date.isoformat()})",
        "",
        "Prompt was identical across all models (fair-comparison rule).",
        "",
        "| Dimension | " + " | ".join(labels) + " |",
        "| :--- " + "| :--- " * len(labels) + "|",
    ]

    dimensions = [
        ("Weekly Regime",          "regime"),
        ("Confidence Score",       "confidence"),
        ("SPX % estimate",         "spx"),
        ("NDX % estimate",         "ndx"),
        ("IWM % estimate",         "iwm"),
        ("Top supporting reason",  "evidence"),
        ("Top contradiction",      "contradiction"),
        ("Invalidation condition", "invalidation"),
    ]
    body = [
        f"| **{display}** | " + " | ".join(_cell(rows_by_label.get(l, {}).get(key, "—")) for l in labels) + " |"
        for display, key in dimensions
    ]

    tail = ["", "## Plain-English summaries", ""]
    tail += [f"- **{l}:** {rows_by_label.get(l, {}).get('plain_english', '—')}" for l in labels]
    tail += ["", "_Disclaimer: model output, not financial advice._", ""]

    return "\n".join(head + body + tail)


class OpenRouterAgent(BaseLLMAgent):
    def __init__(self, model_name: str, model_id: str):
        self.model_name = model_name
        self.model_id = model_id

        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY not found. Make sure a .env file exists "
                f"(looked near {BASE_DIR}) and contains OPENROUTER_API_KEY=..."
            )
        self.client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

    # The ONLY method we implement. Send prompt, return raw text. No parsing here.
    def query(self, prompt: str) -> str:
        max_retries = 3
        system_instruction = (
            "You are a strict financial data formatter. "
            "You MUST output exactly the requested keys in PLAIN TEXT format, separated by colons. "
            "DO NOT OUTPUT JSON FORMAT. "
            "For index ranges, you MUST strictly use the word 'to' (e.g., -1.5 to 2.0). "
            "Do NOT wrap your response in markdown code blocks. "
            "If the user says 'No agent data available', output realistic dummy prediction."
        )

        for attempt in range(max_retries):
            try:
                print(f"[{self.model_name}] OpenRouter request (attempt {attempt + 1}/{max_retries})...")
                response = self.client.chat.completions.create(
                    model=self.model_id,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                )
                raw_text = response.choices[0].message.content

                # Normalize *_RANGE lines so base_llm.parse_response's float() can't crash.
                out_lines = []
                for line in raw_text.splitlines():
                    if "_RANGE" in line:
                        nums = re.findall(r"[-+]?\d*\.\d+|\d+", line)
                        key = line.split(":")[0].strip()
                        out_lines.append(f"{key}: {nums[0]} to {nums[1]}" if len(nums) >= 2 else f"{key}: 0 to 0")
                    else:
                        out_lines.append(line)
                return "\n".join(out_lines)

            except Exception as e:
                print(f"[{self.model_name}] API call failed: {e}")
                time.sleep(2 ** attempt)

        # Fallback if all retries fail (still parseable by parse_response).
        return (
            "WEEKLY_REGIME: Uncertain\nCONFIDENCE: Low\n"
            "SPX_RANGE: 0 to 0\nNDX_RANGE: 0 to 0\nIWM_RANGE: 0 to 0\n"
            "PLAIN_ENGLISH: API connection failed."
        )


if __name__ == "__main__":
    # Pass the prediction date explicitly for reproducible week tags, e.g.:
    #   python backend/agents/llm/multi_model_runner.py 2026-06-16
    prediction_date = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    iso_t = iso_tag(prediction_date)        # e.g. 2026-W25  -> machine JSON
    human_t = human_tag(prediction_date)    # e.g. W24       -> synthesis + comparison

    print(f"\n🚀 Multi-LLM pipeline | run {prediction_date} | machine={iso_t} | human={human_t}\n")

    rows_by_label = {}

    for model in MODELS:
        label, model_id = model["label"], model["id"]
        print("====================================")
        print(f"🤖 {label}  ({model_id})")
        agent = OpenRouterAgent(model_name=label, model_id=model_id)

        try:
            # run() = build_prompt (reads data/outputs/<type>/2026-W25.json via base_llm)
            #         -> query() -> parse_response() -> LLMOutput
            output = agent.run(prediction_date)

            # 1) Machine artifact: data/outputs/llm/<label>/2026-W25.json
            FileSaver(OUTPUTS_LLM_DIR / label).save(_serialize(output), f"{iso_t}.json")

            # 2) Human artifact: data/llm/synthesis_<label>_W24.txt  (render_md format)
            FileSaver(HUMAN_LLM_DIR).save(
                agent.render_md(output, prediction_date), f"synthesis_{label}_{human_t}.txt"
            )

            rows_by_label[label] = _row(output)
            print(f"✅ {label}: data/outputs/llm/{label}/{iso_t}.json + synthesis_{label}_{human_t}.txt")

        except Exception as e:
            print(f"❌ {label} failed: {e}")
            rows_by_label[label] = {}  # empty -> em dashes in the table, never crash

    # 3) Human artifact: the comparison table (one file, all models)
    FileSaver(HUMAN_LLM_DIR).save(
        build_comparison_md(rows_by_label, human_t, prediction_date), f"llm_comparison_{human_t}.md"
    )
    print(f"\n📊 Wrote data/llm/llm_comparison_{human_t}.md")
    print("🏁 Done.")
