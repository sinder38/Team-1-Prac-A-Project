"""Pipeline entry point. Run with: uv run python run_pipeline.py"""

import sys
import tomllib
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.pipeline.context import PipelineContext
from agents.pipeline.stages import (
    LLM_REGISTRY,
    run_almanac,
    run_evidence,
    run_llm,
    run_macro,
    run_technical,
)

_ci_toml = Path(__file__).parent / "pipeline.ci.toml"
_dev_toml = Path(__file__).parent / "pipeline.toml"
PIPELINE_TOML = _ci_toml if _ci_toml.exists() else _dev_toml

REPO_ROOT = Path(__file__).parent.parent


def resolve_date(value: str) -> date:
    if value == "auto":
        return date.today()
    return date.fromisoformat(value)


def main() -> None:
    with open(PIPELINE_TOML, "rb") as f:
        config = tomllib.load(f)

    prediction_date = resolve_date(config["pipeline"]["prediction_date"])
    stages = config["stages"]
    models = config["llm"]["models"]

    ctx = PipelineContext(prediction_date=prediction_date)

    stage_map = {
        "almanac": run_almanac,
        "technical": run_technical,
        "macro": run_macro,
        "evidence": run_evidence,
    }

    for name, fn in stage_map.items():
        if not stages.get(name, False):
            print(f"[pipeline] skipping {name} (disabled in config)")
            continue
        print(f"[pipeline] running {name}...")
        try:
            fn(ctx, config)
        except Exception as e:
            print(f"[pipeline] ERROR in {name}: {e}", file=sys.stderr)
            sys.exit(1)
        print(f"[pipeline] {name} done.")

    rows_by_slug: dict[str, dict] = {}
    for model_key in models:
        if model_key not in LLM_REGISTRY:
            print(f"[pipeline] ERROR: unknown LLM model '{model_key}'", file=sys.stderr)
            sys.exit(1)
        print(f"[pipeline] running llm:{model_key}...")
        try:
            slug, row = run_llm(ctx, config, model_key)
            rows_by_slug[slug] = row
        except Exception as e:
            print(f"[pipeline] ERROR in llm:{model_key}: {e}", file=sys.stderr)
            sys.exit(1)
        print(f"[pipeline] llm:{model_key} done.")

    # Write comparison table if any LLMs ran
    if rows_by_slug and config.get("artifacts", {}).get("save_md", True):
        from agents.io import FileSaver, week_stem
        from agents.llm.multi_model_runner import build_comparison_md

        tag = week_stem(prediction_date)
        comparison_md = build_comparison_md(rows_by_slug, tag, prediction_date)
        FileSaver(REPO_ROOT / "data" / "llm").save(
            comparison_md, f"llm_comparison_{tag}.md"
        )
        print(f"[pipeline] wrote data/llm/llm_comparison_{tag}.md")

    print(
        f"\n[pipeline] complete. date={prediction_date}, llm_outputs={len(ctx.llm_outputs)}"
    )


if __name__ == "__main__":
    main()
