"""Pipeline entry point.

Usage:
    uv run python run_pipeline.py
    uv run python run_pipeline.py --config pipeline.ci.toml
"""

import argparse
import sys
from datetime import date
from pathlib import Path

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).parent))

from agents.pipeline.config import load_config
from agents.pipeline.context import PipelineContext
from agents.pipeline.stages import (
    run_almanac,
    run_evidence,
    run_llm,
    run_macro,
    run_technical,
)

REPO_ROOT = Path(__file__).parent.parent
DEFAULT_CONFIG = Path(__file__).parent / "pipeline.toml"


def resolve_date(value: str) -> date:
    if value == "auto":
        return date.today()
    return date.fromisoformat(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Path to pipeline TOML config (default: pipeline.toml)",
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"[pipeline] ERROR: config file not found: {args.config}", file=sys.stderr)
        sys.exit(1)
    except ValidationError as e:
        print(f"[pipeline] ERROR: invalid config:\n{e}", file=sys.stderr)
        sys.exit(1)

    prediction_date = resolve_date(config.pipeline.prediction_date)

    ctx = PipelineContext(prediction_date=prediction_date)

    stage_map = {
        "almanac": (config.stages.almanac, run_almanac),
        "technical": (config.stages.technical, run_technical),
        "macro": (config.stages.macro, run_macro),
        "evidence": (config.stages.evidence, run_evidence),
    }

    for name, (enabled, fn) in stage_map.items():
        if not enabled:
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
    for entry in config.llm.models:
        print(f"[pipeline] running llm:{entry.slug}...")
        try:
            slug, row = run_llm(ctx, config, entry)
            rows_by_slug[slug] = row
        except Exception as e:
            print(f"[pipeline] ERROR in llm:{entry.slug}: {e}", file=sys.stderr)
            sys.exit(1)
        print(f"[pipeline] llm:{entry.slug} done.")

    # Write comparison table if any LLMs ran
    if rows_by_slug and config.artifacts.save_md:
        from agents.io import FileSaver, week_stem
        from agents.llm.multi_model_runner import build_comparison_md

        tag = week_stem(prediction_date)
        comparison_md = build_comparison_md(rows_by_slug, config.llm.models, tag, prediction_date)
        FileSaver(REPO_ROOT / "data" / "llm").save(
            comparison_md, f"llm_comparison_{tag}.md"
        )
        print(f"[pipeline] wrote data/llm/llm_comparison_{tag}.md")

    print(
        f"\n[pipeline] complete. date={prediction_date}, llm_outputs={len(ctx.llm_outputs)}"
    )


if __name__ == "__main__":
    main()
