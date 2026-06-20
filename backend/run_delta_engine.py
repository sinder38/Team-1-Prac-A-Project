"""Run the Week 5 Delta Engine.

This script reads the vW24 locked prediction and W25 actuals, then writes the
teacher-required delta file to data/qa/delta_W24.md.
"""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from agents.delta import DeltaEngine

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate delta_W24.md")
    parser.add_argument(
        "--prediction-path",
        type=Path,
        default=REPO_ROOT / "data" / "final prediction" / "prediction_2026-W24_Team1.md",
        help="Locked vW24 prediction markdown file",
    )
    parser.add_argument(
        "--actuals-path",
        type=Path,
        default=REPO_ROOT / "data" / "evidence" / "actuals_W25.md",
        help="Matching actuals markdown file for the week after vW24",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=REPO_ROOT / "data" / "qa" / "delta_W24.md",
        help="Output markdown file",
    )
    args = parser.parse_args()

    engine = DeltaEngine(repo_root=REPO_ROOT)
    report = engine.run(
        prediction_path=args.prediction_path,
        actuals_path=args.actuals_path,
        prediction_week="vW24",
        actuals_week="W25",
    )
    engine.write_markdown(report, args.output_path)
    print(f"Wrote {args.output_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
