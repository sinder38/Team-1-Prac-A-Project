"""Calculate weekly accuracy and next-sprint weight suggestions."""

from typing import Mapping

from agents.delta.models import (
    AGENT_ORDER,
    ASSET_LABELS,
    BASE_WEIGHTS,
    SECTOR_ASSETS,
    TRACKED_ASSETS,
    ActualRow,
    DeltaRow,
    PredictionRow,
    WeekAccuracy,
    WeightAdjustment,
    percentage,
)

LOW_ACCURACY_THRESHOLD = 60.0
MIN_AGENT_WEIGHT = 0.05
WEIGHT_STEP = 0.05


def score_available_assets(
    predictions: Mapping[str, PredictionRow],
    actuals: Mapping[str, ActualRow],
) -> tuple[list[DeltaRow], list[str], list[str]]:
    """Score matching rows and record which required rows are missing."""
    rows: list[DeltaRow] = []
    missing_predictions: list[str] = []
    missing_actuals: list[str] = []

    # Check assets in one fixed order so the report is stable each time.
    for asset in TRACKED_ASSETS:
        if asset not in predictions:
            missing_predictions.append(asset)
            continue
        if asset not in actuals:
            missing_actuals.append(asset)
            continue
        rows.append(score_asset(predictions[asset], actuals[asset]))

    return rows, missing_predictions, missing_actuals


def score_asset(prediction: PredictionRow, actual: ActualRow) -> DeltaRow:
    """Compare one predicted direction and range with its actual move."""
    range_hit: bool | None = None
    error_percent: float | None = None

    # Range scoring is optional because some sector predictions only include
    # a direction. In that case both values remain None and the report says N/A.
    if prediction.range_low is not None and prediction.range_high is not None:
        range_hit = prediction.range_low <= actual.actual_move <= prediction.range_high
        if range_hit:
            error_percent = 0.0
        elif actual.actual_move < prediction.range_low:
            error_percent = prediction.range_low - actual.actual_move
        else:
            error_percent = actual.actual_move - prediction.range_high

    predicted_directions = prediction.direction.upper().split("-")
    direction_correct = actual.actual_direction in predicted_directions

    return DeltaRow(
        asset=prediction.asset,
        predicted_direction=prediction.direction,
        predicted_range=_format_range(
            prediction.range_low,
            prediction.range_high,
        ),
        confidence=prediction.confidence,
        actual_move=actual.actual_move,
        actual_direction=actual.actual_direction,
        direction_correct=direction_correct,
        range_hit=range_hit,
        error_percent=(round(error_percent, 2) if error_percent is not None else None),
    )


def summarize_week(
    prediction_week: str,
    actuals_week: str,
    rows: list[DeltaRow],
) -> WeekAccuracy:
    """Combine individual asset results into one weekly score."""
    errors: list[float] = []
    direction_hits = 0
    ranged_assets = 0
    range_hits = 0

    for row in rows:
        if row.direction_correct:
            direction_hits += 1
        if row.range_hit is not None:
            ranged_assets += 1
        if row.range_hit is True:
            range_hits += 1
        if row.error_percent is not None:
            errors.append(row.error_percent)

    return WeekAccuracy(
        prediction_week=prediction_week,
        actuals_week=actuals_week,
        scored_assets=len(rows),
        direction_hits=direction_hits,
        ranged_assets=ranged_assets,
        range_hits=range_hits,
        average_range_error=(round(sum(errors) / len(errors), 2) if errors else 0.0),
    )


def suggest_weight_adjustments(
    rows: list[DeltaRow],
    history: list[WeekAccuracy],
    current_weights: Mapping[str, float],
) -> list[WeightAdjustment]:
    """Suggest small weight changes using cumulative accuracy."""
    suggested: dict[str, float] = {}
    reasons: dict[str, str] = {}
    for agent in AGENT_ORDER:
        suggested[agent] = float(current_weights.get(agent, BASE_WEIGHTS[agent]))
        reasons[agent] = "No change from the previous reviewed weights."

    total_direction_hits = 0
    total_scored_assets = 0
    total_range_hits = 0
    total_ranged_assets = 0
    for week in history:
        total_direction_hits += week.direction_hits
        total_scored_assets += week.scored_assets
        total_range_hits += week.range_hits
        total_ranged_assets += week.ranged_assets

    direction_accuracy = percentage(total_direction_hits, total_scored_assets)
    range_accuracy = percentage(total_range_hits, total_ranged_assets)

    # A five percentage-point transfer is intentionally small. Delta gives the
    # team a trial suggestion rather than silently making a large decision.
    if direction_accuracy < LOW_ACCURACY_THRESHOLD:
        _transfer_weight(suggested, "llm", "human_score")
        reasons["llm"] = (
            "Cumulative direction accuracy is below 60%, so automated "
            "consensus receives a small trial reduction."
        )
        reasons["human_score"] = (
            "Cumulative direction accuracy is below 60%, so final human "
            "challenge and review receive a small trial increase."
        )

    if total_ranged_assets and range_accuracy < LOW_ACCURACY_THRESHOLD:
        _transfer_weight(suggested, "almanac", "technical")
        reasons["almanac"] = (
            "Cumulative range accuracy is below 60%, so broad seasonality "
            "receives a small trial reduction."
        )
        reasons["technical"] = (
            "Cumulative range accuracy is below 60%, so support, resistance, "
            "and volatility checks receive a small trial increase."
        )

    all_directions_correct = bool(rows)
    for row in rows:
        if not row.direction_correct:
            all_directions_correct = False
            break

    if all_directions_correct:
        reasons["macro"] = (
            "The latest direction score was stable, so macro weight stays "
            "unchanged until another completed week is available."
        )

    adjustments: list[WeightAdjustment] = []
    for agent in AGENT_ORDER:
        adjustment = WeightAdjustment(
            agent=agent,
            current_weight=round(
                float(current_weights.get(agent, BASE_WEIGHTS[agent])),
                2,
            ),
            suggested_weight=round(suggested[agent], 2),
            reason=reasons[agent],
        )
        adjustments.append(adjustment)
    return adjustments


def build_prescription(
    rows: list[DeltaRow],
    missing_prediction_assets: list[str],
    adjustments: list[WeightAdjustment],
) -> str:
    """Turn the score and weight changes into practical next-week actions."""
    actions: list[str] = []
    wrong_directions: list[str] = []
    missed_ranges: list[str] = []
    for row in rows:
        if not row.direction_correct:
            wrong_directions.append(row.asset)
        if row.range_hit is False:
            missed_ranges.append(row.asset)

    if wrong_directions:
        actions.append(
            "Review the direction logic for "
            f"{join_assets(wrong_directions)} before the next lock."
        )
    if missed_ranges:
        actions.append(
            f"Recheck volatility and range width for {join_assets(missed_ranges)}."
        )
    if missing_prediction_assets:
        actions.append(
            "Add explicit direction rows for "
            f"{join_assets(missing_prediction_assets)} so every required "
            "sector can be scored."
        )

    changed: list[WeightAdjustment] = []
    for item in adjustments:
        if item.current_weight != item.suggested_weight:
            changed.append(item)
    if changed:
        change_texts: list[str] = []
        for item in changed:
            change_texts.append(
                f"{item.agent} {item.current_weight:.2f} to {item.suggested_weight:.2f}"
            )
        changes = ", ".join(change_texts)
        actions.append(f"Use these small trial weights next sprint: {changes}.")
    if not actions:
        return (
            "Keep the reviewed weights for one more sprint and collect "
            "another completed result before making a larger change."
        )
    return " ".join(actions)


def sector_coverage(rows: list[DeltaRow]) -> int:
    count = 0
    for row in rows:
        if row.asset in SECTOR_ASSETS:
            count += 1
    return count


def join_assets(assets: list[str]) -> str:
    labels: list[str] = []
    for item in assets:
        labels.append(f"{ASSET_LABELS[item]} ({item})")
    if not labels:
        return "none"
    if len(labels) == 1:
        return labels[0]
    return f"{', '.join(labels[:-1])} and {labels[-1]}"


def _format_range(low: float | None, high: float | None) -> str:
    if low is None or high is None:
        return "Not provided"
    return f"{low:+.1f}% to {high:+.1f}%"


def _transfer_weight(
    weights: dict[str, float],
    source: str,
    target: str,
) -> None:
    """Move one small amount while keeping the source above its minimum."""
    available = max(0.0, weights[source] - MIN_AGENT_WEIGHT)
    transfer = min(WEIGHT_STEP, available)
    weights[source] -= transfer
    weights[target] += transfer
