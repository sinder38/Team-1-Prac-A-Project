"""Calculate weekly accuracy and next-sprint weight suggestions."""

from typing import Mapping

from agents.delta.models import (
    ActualRow,
    AGENT_ORDER,
    ASSET_LABELS,
    BASE_WEIGHTS,
    DeltaRow,
    PredictionRow,
    SECTOR_ASSETS,
    TRACKED_ASSETS,
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
    rows = [
        score_asset(predictions[asset], actuals[asset])
        for asset in TRACKED_ASSETS
        if asset in predictions and asset in actuals
    ]
    missing_predictions = [
        asset for asset in TRACKED_ASSETS if asset not in predictions
    ]
    missing_actuals = [
        asset
        for asset in TRACKED_ASSETS
        if asset in predictions and asset not in actuals
    ]
    return rows, missing_predictions, missing_actuals


def score_asset(prediction: PredictionRow, actual: ActualRow) -> DeltaRow:
    range_hit: bool | None = None
    error_percent: float | None = None
    if prediction.range_low is not None and prediction.range_high is not None:
        range_hit = (
            prediction.range_low
            <= actual.actual_move
            <= prediction.range_high
        )
        if range_hit:
            error_percent = 0.0
        elif actual.actual_move < prediction.range_low:
            error_percent = prediction.range_low - actual.actual_move
        else:
            error_percent = actual.actual_move - prediction.range_high

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
        direction_correct=(
            actual.actual_direction in prediction.direction.upper().split("-")
        ),
        range_hit=range_hit,
        error_percent=(
            round(error_percent, 2) if error_percent is not None else None
        ),
    )


def summarize_week(
    prediction_week: str,
    actuals_week: str,
    rows: list[DeltaRow],
) -> WeekAccuracy:
    errors = [
        row.error_percent
        for row in rows
        if row.error_percent is not None
    ]
    return WeekAccuracy(
        prediction_week=prediction_week,
        actuals_week=actuals_week,
        scored_assets=len(rows),
        direction_hits=sum(row.direction_correct for row in rows),
        ranged_assets=sum(row.range_hit is not None for row in rows),
        range_hits=sum(row.range_hit is True for row in rows),
        average_range_error=(
            round(sum(errors) / len(errors), 2) if errors else 0.0
        ),
    )


def suggest_weight_adjustments(
    rows: list[DeltaRow],
    history: list[WeekAccuracy],
    current_weights: Mapping[str, float],
) -> list[WeightAdjustment]:
    suggested = {
        agent: float(current_weights.get(agent, BASE_WEIGHTS[agent]))
        for agent in AGENT_ORDER
    }
    reasons = {
        agent: "No change from the previous reviewed weights."
        for agent in AGENT_ORDER
    }

    direction_accuracy = percentage(
        sum(week.direction_hits for week in history),
        sum(week.scored_assets for week in history),
    )
    ranged_assets = sum(week.ranged_assets for week in history)
    range_accuracy = percentage(
        sum(week.range_hits for week in history),
        ranged_assets,
    )

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

    if ranged_assets and range_accuracy < LOW_ACCURACY_THRESHOLD:
        _transfer_weight(suggested, "almanac", "technical")
        reasons["almanac"] = (
            "Cumulative range accuracy is below 60%, so broad seasonality "
            "receives a small trial reduction."
        )
        reasons["technical"] = (
            "Cumulative range accuracy is below 60%, so support, resistance, "
            "and volatility checks receive a small trial increase."
        )

    if rows and all(row.direction_correct for row in rows):
        reasons["macro"] = (
            "The latest direction score was stable, so macro weight stays "
            "unchanged until another completed week is available."
        )

    return [
        WeightAdjustment(
            agent=agent,
            current_weight=round(
                float(current_weights.get(agent, BASE_WEIGHTS[agent])),
                2,
            ),
            suggested_weight=round(suggested[agent], 2),
            reason=reasons[agent],
        )
        for agent in AGENT_ORDER
    ]


def build_prescription(
    rows: list[DeltaRow],
    missing_prediction_assets: list[str],
    adjustments: list[WeightAdjustment],
) -> str:
    actions: list[str] = []
    wrong_directions = [
        row.asset for row in rows if not row.direction_correct
    ]
    missed_ranges = [row.asset for row in rows if row.range_hit is False]

    if wrong_directions:
        actions.append(
            "Review the direction logic for "
            f"{join_assets(wrong_directions)} before the next lock."
        )
    if missed_ranges:
        actions.append(
            "Recheck volatility and range width for "
            f"{join_assets(missed_ranges)}."
        )
    if missing_prediction_assets:
        actions.append(
            "Add explicit direction rows for "
            f"{join_assets(missing_prediction_assets)} so every required "
            "sector can be scored."
        )

    changed = [
        item
        for item in adjustments
        if item.current_weight != item.suggested_weight
    ]
    if changed:
        changes = ", ".join(
            f"{item.agent} {item.current_weight:.2f} to "
            f"{item.suggested_weight:.2f}"
            for item in changed
        )
        actions.append(f"Use these small trial weights next sprint: {changes}.")
    if not actions:
        return (
            "Keep the reviewed weights for one more sprint and collect "
            "another completed result before making a larger change."
        )
    return " ".join(actions)


def sector_coverage(rows: list[DeltaRow]) -> int:
    return sum(row.asset in SECTOR_ASSETS for row in rows)


def join_assets(assets: list[str]) -> str:
    labels = [f"{ASSET_LABELS[item]} ({item})" for item in assets]
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
    available = max(0.0, weights[source] - MIN_AGENT_WEIGHT)
    transfer = min(WEIGHT_STEP, available)
    weights[source] -= transfer
    weights[target] += transfer
