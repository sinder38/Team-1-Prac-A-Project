"""Run the Week 5 Delta Engine.

This script reads the vW24 locked prediction and W25 actuals, then writes the
teacher-required delta file to data/qa/delta_W24.md.
"""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from agents.delta import DeltaAgent

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate delta_W24.md")
    parser.add_argument(
        "--prediction-week",
        default="W24",
        help="Locked prediction week to score, e.g. W24",
    )
    parser.add_argument(
        "--actuals-week",
        default="W25",
        help="Actuals week that matches the prediction result, e.g. W25",
    )
    parser.add_argument(
        "--prediction-path",
        type=Path,
        default=None,
        help="Locked vW24 prediction markdown file",
    )
    parser.add_argument(
        "--actuals-path",
        type=Path,
        default=None,
        help="Matching actuals markdown file for the week after vW24",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=None,
        help="Output markdown file. Defaults to data/qa/delta_<prediction-week>.md",
    )
    parser.add_argument(
        "--json-output-path",
        type=Path,
        default=None,
        help="Structured Delta Engine output. Defaults to data/outputs/delta/delta_<prediction-week>.json",
    )
    args = parser.parse_args()

    agent = DeltaAgent(repo_root=REPO_ROOT)
    report = agent.run(
        prediction_week=args.prediction_week,
        actuals_week=args.actuals_week,
        prediction_path=args.prediction_path,
        actuals_path=args.actuals_path,
    )
    markdown_path, json_path = agent.write_outputs(
        report,
        markdown_path=args.output_path,
        json_path=args.json_output_path,
    )
    print(f"Wrote {markdown_path.relative_to(REPO_ROOT)}")
    print(f"Wrote {json_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
