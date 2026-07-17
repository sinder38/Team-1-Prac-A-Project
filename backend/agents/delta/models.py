"""Shared data models and constants for the Delta Engine."""

from dataclasses import dataclass
from typing import Any

CORE_ASSETS = ("SPX", "NDX", "IWM")
SECTOR_ASSETS = (
    "XLK",
    "XLV",
    "XLF",
    "XLY",
    "XLC",
    "XLI",
    "XLP",
    "XLE",
    "XLB",
    "XLRE",
    "XLU",
)
TRACKED_ASSETS = CORE_ASSETS + SECTOR_ASSETS

ASSET_LABELS = {
    "SPX": "S&P 500",
    "NDX": "Nasdaq 100",
    "IWM": "Russell 2000",
    "XLK": "Technology",
    "XLV": "Health Care",
    "XLF": "Financials",
    "XLY": "Consumer Discretionary",
    "XLC": "Communication Services",
    "XLI": "Industrials",
    "XLP": "Consumer Staples",
    "XLE": "Energy",
    "XLB": "Materials",
    "XLRE": "Real Estate",
    "XLU": "Utilities",
}

AGENT_ORDER = ("almanac", "macro", "technical", "llm", "human_score")
BASE_WEIGHTS = {
    "almanac": 0.20,
    "macro": 0.20,
    "technical": 0.25,
    "llm": 0.20,
    "human_score": 0.15,
}


@dataclass(frozen=True)
class PredictionRow:
    asset: str
    direction: str
    range_low: float | None
    range_high: float | None
    confidence: str


@dataclass(frozen=True)
class ActualRow:
    asset: str
    actual_move: float
    actual_direction: str


@dataclass(frozen=True)
class DeltaRow:
    asset: str
    predicted_direction: str
    predicted_range: str
    confidence: str
    actual_move: float
    actual_direction: str
    direction_correct: bool
    range_hit: bool | None
    error_percent: float | None


@dataclass(frozen=True)
class WeekAccuracy:
    prediction_week: str
    actuals_week: str
    scored_assets: int
    direction_hits: int
    ranged_assets: int
    range_hits: int
    average_range_error: float

    @property
    def direction_accuracy(self) -> float:
        return percentage(self.direction_hits, self.scored_assets)

    @property
    def range_accuracy(self) -> float | None:
        if not self.ranged_assets:
            return None
        return percentage(self.range_hits, self.ranged_assets)


@dataclass(frozen=True)
class WeightAdjustment:
    agent: str
    current_weight: float
    suggested_weight: float
    reason: str


@dataclass(frozen=True)
class DeltaReport:
    schema_version: int
    prediction_week: str
    actuals_week: str
    rows: list[DeltaRow]
    missing_prediction_assets: list[str]
    missing_actual_assets: list[str]
    history: list[WeekAccuracy]
    history_notes: list[str]
    weight_adjustments: list[WeightAdjustment]
    prescription: str

    @property
    def direction_correct_count(self) -> int:
        return sum(row.direction_correct for row in self.rows)

    @property
    def ranged_asset_count(self) -> int:
        return sum(row.range_hit is not None for row in self.rows)

    @property
    def range_hit_count(self) -> int:
        return sum(row.range_hit is True for row in self.rows)

    @property
    def average_error_percent(self) -> float:
        errors = [
            row.error_percent
            for row in self.rows
            if row.error_percent is not None
        ]
        if not errors:
            return 0.0
        return round(sum(errors) / len(errors), 2)

    @property
    def cumulative_direction_accuracy(self) -> float:
        hits = sum(week.direction_hits for week in self.history)
        total = sum(week.scored_assets for week in self.history)
        return percentage(hits, total)

    @property
    def cumulative_range_accuracy(self) -> float | None:
        hits = sum(week.range_hits for week in self.history)
        total = sum(week.ranged_assets for week in self.history)
        if not total:
            return None
        return percentage(hits, total)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeltaReport":
        """Rebuild a report loaded from the structured JSON artifact."""
        return cls(
            schema_version=int(data["schema_version"]),
            prediction_week=str(data["prediction_week"]),
            actuals_week=str(data["actuals_week"]),
            rows=[DeltaRow(**item) for item in data.get("rows", [])],
            missing_prediction_assets=list(
                data.get("missing_prediction_assets", [])
            ),
            missing_actual_assets=list(data.get("missing_actual_assets", [])),
            history=[
                WeekAccuracy(**item) for item in data.get("history", [])
            ],
            history_notes=list(data.get("history_notes", [])),
            weight_adjustments=[
                WeightAdjustment(**item)
                for item in data.get("weight_adjustments", [])
            ],
            prescription=str(data.get("prescription", "")),
        )


def percentage(numerator: int, denominator: int) -> float:
    if not denominator:
        return 0.0
    return round(numerator / denominator * 100.0, 1)
