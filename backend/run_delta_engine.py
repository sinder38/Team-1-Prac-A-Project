"""Run the Delta Engine for one completed prediction week."""

import argparse
from pathlib import Path

from agents.delta import DeltaAgent

REPO_ROOT = Path(__file__).resolve().parents[1]


def display_path(path: Path) -> Path:
    """Show repository paths briefly while allowing custom output folders."""
    try:
        return path.relative_to(REPO_ROOT)
    except ValueError:
        return path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Score a locked prediction against matching actuals."
    )
    parser.add_argument(
        "--prediction-week",
        required=True,
        help="Locked prediction week, for example W28",
    )
    parser.add_argument(
        "--actuals-week",
        required=True,
        help="Following completed actuals week, for example W29",
    )
    parser.add_argument("--prediction-path", type=Path)
    parser.add_argument("--actuals-path", type=Path)
    parser.add_argument("--output-path", type=Path)
    parser.add_argument("--json-output-path", type=Path)
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
    print(f"Wrote {display_path(markdown_path)}")
    print(f"Wrote {display_path(json_path)}")


if __name__ == "__main__":
    main()
