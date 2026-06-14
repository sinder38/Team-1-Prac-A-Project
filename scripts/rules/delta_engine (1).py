"""
delta_engine.py
Computes prediction accuracy for each week by comparing
prediction files against actual market outcomes.

Usage:
    python delta_engine.py --week W24
    python delta_engine.py --all
"""

import json
import os
import argparse
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────
PREDICTIONS_DIR = Path("data/predictions")
ACTUALS_DIR = Path("data/actuals")
OUTPUT_DIR = Path("data/delta")

# Assets tracked every week
TRACKED_ASSETS = ["SPX", "NDX", "IWM", "Gold", "WTI", "VIX", "Bitcoin"]

# ── Data Format ───────────────────────────────────────────────────────────────
# Prediction file: data/predictions/prediction_W24.json
# {
#   "week": "W24",
#   "assets": {
#     "SPX":     {"direction": "DOWN", "range_low": -3.0, "range_high": -1.0},
#     "NDX":     {"direction": "DOWN", "range_low": -4.0, "range_high": -1.5},
#     "IWM":     {"direction": "DOWN", "range_low": -3.5, "range_high": -1.0},
#     "Gold":    {"direction": "FLAT-UP", "range_low": -1.0, "range_high": 2.0},
#     "WTI":     {"direction": "UP",   "range_low": 0.0,  "range_high": 4.0},
#     "VIX":     {"direction": "UP",   "range_low": 0.0,  "range_high": 20.0},
#     "Bitcoin": {"direction": "DOWN", "range_low": -8.0, "range_high": -2.0}
#   }
# }

# Actuals file: data/actuals/actuals_W24.json
# {
#   "week": "W24",
#   "assets": {
#     "SPX":     {"actual_change": 0.46},
#     "NDX":     {"actual_change": 2.17},
#     "IWM":     {"actual_change": 3.93},
#     "Gold":    {"actual_change": -2.90},
#     "WTI":     {"actual_change": -6.25},
#     "VIX":     {"actual_change": -6.25},
#     "Bitcoin": {"actual_change": 5.24}
#   }
# }


def get_direction(actual_change: float) -> str:
    """Convert actual % change to direction label."""
    if actual_change > 0.15:
        return "UP"
    elif actual_change < -0.15:
        return "DOWN"
    else:
        return "FLAT"


def direction_hit(predicted: str, actual_change: float) -> bool:
    """Check if predicted direction matches actual direction."""
    actual_dir = get_direction(actual_change)

    if predicted == "UP":
        return actual_dir == "UP"
    elif predicted == "DOWN":
        return actual_dir == "DOWN"
    elif predicted in ("FLAT", "FLAT-UP"):
        return actual_dir in ("FLAT", "UP")
    elif predicted == "FLAT-DOWN":
        return actual_dir in ("FLAT", "DOWN")
    return False


def range_hit(range_low: float, range_high: float, actual_change: float) -> bool:
    """Check if actual % change fell within predicted range."""
    return range_low <= actual_change <= range_high


def compute_week_delta(week: str) -> dict:
    """Compute accuracy for a single week."""
    pred_file = PREDICTIONS_DIR / f"prediction_{week}.json"
    actual_file = ACTUALS_DIR / f"actuals_{week}.json"

    if not pred_file.exists():
        raise FileNotFoundError(f"Prediction file not found: {pred_file}")
    if not actual_file.exists():
        raise FileNotFoundError(f"Actuals file not found: {actual_file}")

    with open(pred_file) as f:
        pred_data = json.load(f)
    with open(actual_file) as f:
        actual_data = json.load(f)

    results = []
    direction_hits = 0
    range_hits = 0
    total = 0

    for asset in TRACKED_ASSETS:
        pred = pred_data["assets"].get(asset)
        actual = actual_data["assets"].get(asset)

        if not pred or not actual:
            continue

        actual_change = actual["actual_change"]
        predicted_dir = pred["direction"]
        range_low = pred.get("range_low", None)
        range_high = pred.get("range_high", None)

        dir_correct = direction_hit(predicted_dir, actual_change)
        rng_correct = (
            range_hit(range_low, range_high, actual_change)
            if range_low is not None and range_high is not None
            else None
        )

        results.append({
            "asset": asset,
            "predicted_direction": predicted_dir,
            "predicted_range": f"{range_low}% to {range_high}%" if range_low is not None else "N/A",
            "actual_change": actual_change,
            "actual_direction": get_direction(actual_change),
            "direction_hit": dir_correct,
            "range_hit": rng_correct,
        })

        if dir_correct:
            direction_hits += 1
        if rng_correct:
            range_hits += 1
        total += 1

    direction_accuracy = round(direction_hits / total * 100, 1) if total > 0 else 0
    range_accuracy = round(range_hits / total * 100, 1) if total > 0 else 0

    return {
        "week": week,
        "total_assets": total,
        "direction_hits": direction_hits,
        "range_hits": range_hits,
        "direction_accuracy_pct": direction_accuracy,
        "range_accuracy_pct": range_accuracy,
        "results": results,
    }


def print_delta_report(delta: dict):
    """Print a formatted weekly delta report."""
    week = delta["week"]
    print(f"\n{'='*60}")
    print(f"  DELTA ENGINE — {week}")
    print(f"{'='*60}")
    print(f"  Direction Accuracy : {delta['direction_hits']}/{delta['total_assets']} ({delta['direction_accuracy_pct']}%)")
    print(f"  Range Accuracy     : {delta['range_hits']}/{delta['total_assets']} ({delta['range_accuracy_pct']}%)")
    print(f"{'='*60}")
    print(f"  {'Asset':<12} {'Predicted':>10} {'Actual':>10} {'Dir':>6} {'Range':>6}")
    print(f"  {'-'*52}")
    for r in delta["results"]:
        dir_mark = "HIT " if r["direction_hit"] else "MISS"
        rng_mark = "HIT " if r["range_hit"] else ("MISS" if r["range_hit"] is False else "N/A ")
        print(
            f"  {r['asset']:<12} "
            f"{r['predicted_direction']:>10} "
            f"{r['actual_change']:>+9.2f}% "
            f"  {dir_mark} "
            f"  {rng_mark}"
        )
    print(f"{'='*60}\n")


def save_delta(delta: dict):
    """Save delta results as JSON."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT_DIR / f"delta_{delta['week']}.json"
    with open(out_file, "w") as f:
        json.dump(delta, f, indent=2)
    print(f"Saved: {out_file}")


def compute_all_deltas():
    """Compute accuracy for all available weeks."""
    if not PREDICTIONS_DIR.exists():
        print(f"Predictions directory not found: {PREDICTIONS_DIR}")
        return

    pred_files = sorted(PREDICTIONS_DIR.glob("prediction_W*.json"))
    if not pred_files:
        print("No prediction files found.")
        return

    all_deltas = []
    for pred_file in pred_files:
        week = pred_file.stem.replace("prediction_", "")
        try:
            delta = compute_week_delta(week)
            print_delta_report(delta)
            save_delta(delta)
            all_deltas.append(delta)
        except FileNotFoundError as e:
            print(f"Skipping {week}: {e}")

    # Running summary
    if all_deltas:
        print(f"\n{'='*60}")
        print("  RUNNING ACCURACY SUMMARY")
        print(f"{'='*60}")
        total_dir = sum(d["direction_hits"] for d in all_deltas)
        total_rng = sum(d["range_hits"] for d in all_deltas)
        total_assets = sum(d["total_assets"] for d in all_deltas)
        print(f"  Weeks tracked      : {len(all_deltas)}")
        print(f"  Direction accuracy : {total_dir}/{total_assets} ({round(total_dir/total_assets*100,1)}%)")
        print(f"  Range accuracy     : {total_rng}/{total_assets} ({round(total_rng/total_assets*100,1)}%)")
        print(f"{'='*60}\n")


# ── Hardcoded W24 data for immediate use ──────────────────────────────────────
# Remove this once JSON files are set up in data/predictions and data/actuals

W24_PREDICTION = {
    "week": "W24",
    "assets": {
        "SPX":     {"direction": "DOWN",    "range_low": -3.0, "range_high": -1.0},
        "NDX":     {"direction": "DOWN",    "range_low": -4.0, "range_high": -1.5},
        "IWM":     {"direction": "DOWN",    "range_low": -3.5, "range_high": -1.0},
        "Gold":    {"direction": "FLAT-UP", "range_low": -1.0, "range_high":  2.0},
        "WTI":     {"direction": "UP",      "range_low":  0.0, "range_high":  4.0},
        "VIX":     {"direction": "UP",      "range_low":  0.0, "range_high": 20.0},
        "Bitcoin": {"direction": "DOWN",    "range_low": -8.0, "range_high": -2.0},
    }
}

W24_ACTUALS = {
    "week": "W24",
    "assets": {
        "SPX":     {"actual_change":  0.46},
        "NDX":     {"actual_change":  2.17},
        "IWM":     {"actual_change":  3.93},
        "Gold":    {"actual_change": -2.90},
        "WTI":     {"actual_change": -6.25},
        "VIX":     {"actual_change": -6.25},
        "Bitcoin": {"actual_change":  5.24},
    }
}


def compute_from_hardcoded(pred_data: dict, actual_data: dict) -> dict:
    """Compute delta from hardcoded dicts (no file I/O needed)."""
    week = pred_data["week"]
    results = []
    direction_hits = 0
    range_hits = 0
    total = 0

    for asset in TRACKED_ASSETS:
        pred = pred_data["assets"].get(asset)
        actual = actual_data["assets"].get(asset)
        if not pred or not actual:
            continue

        actual_change = actual["actual_change"]
        predicted_dir = pred["direction"]
        range_low = pred.get("range_low")
        range_high = pred.get("range_high")

        dir_correct = direction_hit(predicted_dir, actual_change)
        rng_correct = (
            range_hit(range_low, range_high, actual_change)
            if range_low is not None and range_high is not None
            else None
        )

        results.append({
            "asset": asset,
            "predicted_direction": predicted_dir,
            "predicted_range": f"{range_low}% to {range_high}%",
            "actual_change": actual_change,
            "actual_direction": get_direction(actual_change),
            "direction_hit": dir_correct,
            "range_hit": rng_correct,
        })

        if dir_correct:
            direction_hits += 1
        if rng_correct:
            range_hits += 1
        total += 1

    direction_accuracy = round(direction_hits / total * 100, 1) if total > 0 else 0
    range_accuracy = round(range_hits / total * 100, 1) if total > 0 else 0

    return {
        "week": week,
        "total_assets": total,
        "direction_hits": direction_hits,
        "range_hits": range_hits,
        "direction_accuracy_pct": direction_accuracy,
        "range_accuracy_pct": range_accuracy,
        "results": results,
    }


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delta Engine — Weekly Prediction Accuracy")
    parser.add_argument("--week", type=str, help="Week to compute (e.g. W24)")
    parser.add_argument("--all", action="store_true", help="Compute all available weeks")
    parser.add_argument("--hardcoded", action="store_true", help="Run W24 from hardcoded data (no files needed)")
    args = parser.parse_args()

    if args.hardcoded or (not args.week and not args.all):
        print("Running W24 from hardcoded data...")
        delta = compute_from_hardcoded(W24_PREDICTION, W24_ACTUALS)
        print_delta_report(delta)
    elif args.all:
        compute_all_deltas()
    elif args.week:
        try:
            delta = compute_week_delta(args.week)
            print_delta_report(delta)
            save_delta(delta)
        except FileNotFoundError as e:
            print(f"Error: {e}")
