"""Read prediction and actuals artifacts used by the Delta Engine."""

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from agents.delta.models import (
    CORE_ASSETS,
    TRACKED_ASSETS,
    ActualRow,
    PredictionRow,
)

ASSET_ALIASES = {
    "S&P 500": "SPX",
    "NASDAQ 100": "NDX",
    "RUSSELL 2000": "IWM",
    "TECHNOLOGY": "XLK",
    "HEALTH CARE": "XLV",
    "HEALTHCARE": "XLV",
    "FINANCIALS": "XLF",
    "CONSUMER DISCRETIONARY": "XLY",
    "COMMUNICATION SERVICES": "XLC",
    "COMMUNICATION": "XLC",
    "INDUSTRIALS": "XLI",
    "CONSUMER STAPLES": "XLP",
    "ENERGY": "XLE",
    "MATERIALS": "XLB",
    "REAL ESTATE": "XLRE",
    "UTILITIES": "XLU",
}
FLAT_MOVE_THRESHOLD = 0.05

# TODO: use Agent parsing instead


def parse_prediction_file(path: Path) -> dict[str, PredictionRow]:
    """Read a locked prediction from either JSON or Markdown."""
    if not path.exists():
        raise FileNotFoundError(f"Prediction file not found: {path}")
    if path.suffix.lower() == ".json":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed prediction JSON: {path}") from exc
        return parse_prediction_json(data)
    return parse_prediction_markdown(path.read_text(encoding="utf-8"))


def parse_actuals_file(path: Path) -> dict[str, ActualRow]:
    """Read the weekly actuals Markdown file."""
    if not path.exists():
        raise FileNotFoundError(f"Actuals file not found: {path}")
    return parse_actuals_markdown(path.read_text(encoding="utf-8"))


def parse_prediction_markdown(markdown: str) -> dict[str, PredictionRow]:
    """Read prediction rows from a Markdown table."""
    rows: dict[str, PredictionRow] = {}
    for line in markdown.splitlines():
        # Headings and paragraphs are ignored. A table row starts with |.
        if not line.lstrip().startswith("|"):
            continue
        cells = _table_cells(line)
        asset_index, asset = _find_asset(cells)
        if not asset:
            continue

        # Only inspect cells after the asset name. This avoids reading a word
        # such as "Technology" as part of another column.
        following = cells[asset_index + 1 :]
        direction = _first_direction(following)
        if not direction:
            continue
        range_low, range_high = _first_range(following)
        rows[asset] = PredictionRow(
            asset=asset,
            direction=direction,
            range_low=range_low,
            range_high=range_high,
            confidence=_first_confidence(following),
        )

    # _require_core_assets(rows, "prediction")
    return rows


def parse_prediction_json(data: Any) -> dict[str, PredictionRow]:
    """Read prediction rows from the JSON formats used by the project."""
    rows: dict[str, PredictionRow] = {}
    for item in _prediction_json_rows(data):
        asset_text = str(
            item.get("asset")
            or item.get("symbol")
            or item.get("ticker")
            or item.get("name")
            or ""
        )
        asset = _asset_from_text(asset_text)
        direction = _normalise_direction(str(item.get("direction", "")))
        if not asset or not direction:
            continue
        range_low, range_high = _range_from_json(item)
        rows[asset] = PredictionRow(
            asset=asset,
            direction=direction,
            range_low=range_low,
            range_high=range_high,
            confidence=_normalise_confidence(str(item.get("confidence", ""))),
        )

    # _require_core_assets(rows, "prediction")
    return rows


def parse_actuals_markdown(markdown: str) -> dict[str, ActualRow]:
    """Read actual percentage moves from a Markdown table."""
    rows: dict[str, ActualRow] = {}
    for line in markdown.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = _table_cells(line)
        asset_index, asset = _find_asset(cells)
        if not asset:
            continue

        # The first percentage after the asset name is the weekly actual move.
        # A normal loop makes this selection easier to follow than next(...).
        actual_text = ""
        for cell in cells[asset_index + 1 :]:
            if "%" in cell and _has_number(cell):
                actual_text = _clean_markdown(cell)
                break
        if not actual_text:
            continue
        move = _parse_single_percent(actual_text)
        rows[asset] = ActualRow(
            asset=asset,
            actual_move=move,
            actual_direction=_actual_direction(actual_text, move),
        )

    # _require_core_assets(rows, "actuals")
    return rows


def plain_week(week: str) -> str:
    """Return a checked week label such as W24."""
    cleaned = week.strip()
    if cleaned.lower().startswith("vw"):
        cleaned = cleaned[1:]
    match = re.fullmatch(r"W(\d{2})", cleaned)
    if not match or not 1 <= int(match.group(1)) <= 53:
        raise ValueError(f"Invalid week label: {week!r}")
    return cleaned


def versioned_week(week: str) -> str:
    return f"v{plain_week(week)}"


def week_number(week: str) -> int:
    return int(plain_week(week)[1:])


def next_week(week: str) -> str:
    """Return the following week label, including the year-end rollover."""
    number = week_number(week)
    return "W01" if number == 53 else f"W{number + 1:02d}"


def validate_week_pair(prediction_week: str, actuals_week: str) -> None:
    """Require actuals from the week immediately after the prediction."""
    expected = next_week(prediction_week)
    if plain_week(actuals_week) != expected:
        raise ValueError(
            f"{plain_week(prediction_week)} can only be scored against "
            f"{expected} actuals, not {plain_week(actuals_week)}."
        )


def artifact_week(prediction_week: str, actuals_week: object | None) -> str:
    """Return the week label used to file Delta artifacts.

    A Delta report belongs to the pipeline run that produced it, and that run
    is identified by the completed actuals week (all sibling artifacts of the
    same run, such as actuals, agent reports, and the LLM comparison,
    carry that label).
    When ``actuals_week`` is missing (legacy payloads predate the field), fall
    back to the week after the prediction. Reject an explicit malformed or
    mismatched value so the filename cannot disagree with the report body.
    """
    fallback = next_week(prediction_week)
    if actuals_week is None:
        return fallback
    if not isinstance(actuals_week, str):
        raise TypeError(f"Week label must be a string, not {actuals_week!r}")
    if not actuals_week.strip():
        return fallback

    validate_week_pair(prediction_week, actuals_week)
    return plain_week(actuals_week)


def _prediction_json_rows(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        rows: list[dict[str, Any]] = []
        for item in data:
            if isinstance(item, dict):
                rows.append(item)
        return rows
    if not isinstance(data, dict):
        return []

    rows: list[dict[str, Any]] = []
    # Different team files use different container names. Support the known
    # names without guessing values from unrelated JSON fields.
    for key in ("predictions", "assets", "indices", "sectors"):
        value = data.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    rows.append(item)
    if rows:
        return rows

    for key, value in data.items():
        if isinstance(value, dict) and _asset_from_text(str(key)):
            rows.append({"asset": key, **value})
    return rows


def _range_from_json(
    item: Mapping[str, Any],
) -> tuple[float | None, float | None]:
    # The application has used separate low/high fields, dictionaries, lists
    # and text ranges. Convert all four forms to the same pair of floats.
    low = item.get("range_low")
    high = item.get("range_high")
    if low is not None and high is not None:
        return _ordered_range(float(low), float(high))

    value = item.get("range")
    if isinstance(value, dict):
        low = value.get("low")
        high = value.get("high")
        if low is not None and high is not None:
            return _ordered_range(float(low), float(high))
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return _ordered_range(float(value[0]), float(value[1]))
    if isinstance(value, str):
        return _parse_percent_range(value)
    return None, None


def _find_asset(cells: list[str]) -> tuple[int, str]:
    for index, cell in enumerate(cells):
        asset = _asset_from_text(cell)
        if asset:
            return index, asset
    return -1, ""


def _asset_from_text(text: str) -> str:
    cleaned = _clean_markdown(text).upper()
    # Check ticker symbols before full names because symbols are unambiguous.
    for asset in TRACKED_ASSETS:
        if re.search(rf"\b{re.escape(asset)}\b", cleaned):
            return asset
    for alias, asset in ASSET_ALIASES.items():
        if alias in cleaned:
            return asset
    return ""


def _first_direction(cells: list[str]) -> str:
    for cell in cells:
        direction = _normalise_direction(cell)
        if direction:
            return direction
    return ""


def _normalise_direction(text: str) -> str:
    cleaned = _clean_markdown(text).upper()
    cleaned = re.sub(r"[\u2013\u2014/]", "-", cleaned)
    cleaned = re.sub(r"\s*-\s*", "-", cleaned)
    accepted_directions = (
        "FLAT-UP",
        "FLAT-DOWN",
        "UP-FLAT",
        "DOWN-FLAT",
        "UP",
        "DOWN",
        "FLAT",
    )
    for direction in accepted_directions:
        if re.search(rf"\b{direction}\b", cleaned):
            # UP-FLAT and FLAT-UP mean the same mixed direction. Return one
            # consistent order so later scoring only needs a simple split.
            if direction == "UP-FLAT":
                return "FLAT-UP"
            if direction == "DOWN-FLAT":
                return "FLAT-DOWN"
            return direction
    aliases = {
        "NEUTRAL-BULLISH": "FLAT-UP",
        "NEUTRAL-BEARISH": "FLAT-DOWN",
        "BULLISH": "UP",
        "BEARISH": "DOWN",
        "NEUTRAL": "FLAT",
    }
    for label, direction in aliases.items():
        if label in cleaned:
            return direction
    return ""


def _first_range(
    cells: list[str],
) -> tuple[float | None, float | None]:
    for cell in cells:
        if "%" in cell:
            low, high = _parse_percent_range(cell)
            if low is not None and high is not None:
                return low, high
    return None, None


def _parse_percent_range(
    text: str,
) -> tuple[float | None, float | None]:
    values: list[float] = []
    matches = re.findall(r"[-+]?\d+(?:\.\d+)?", text)
    for value in matches:
        values.append(float(value))
    if len(values) < 2:
        return None, None
    return _ordered_range(values[0], values[1])


def _ordered_range(low: float, high: float) -> tuple[float, float]:
    return min(low, high), max(low, high)


def _first_confidence(cells: list[str]) -> str:
    for cell in cells:
        confidence = _normalise_confidence(cell)
        if confidence != "Not provided":
            return confidence
    return "Not provided"


def _normalise_confidence(text: str) -> str:
    cleaned = _clean_markdown(text).upper().replace("_", "-")
    if "LOW-MEDIUM" in cleaned or "LOW MEDIUM" in cleaned:
        return "Low-Medium"
    if "MEDIUM-HIGH" in cleaned or "MEDIUM HIGH" in cleaned:
        return "Medium-High"
    for value in ("HIGH", "MEDIUM", "LOW"):
        if re.search(rf"\b{value}\b", cleaned):
            return value.title()
    return "Not provided"


def _parse_single_percent(text: str) -> float:
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    if not match:
        raise ValueError(f"Could not read actual percentage: {text!r}")
    value = float(match.group(0))
    if "down" in text.lower() and value > 0:
        return -value
    return value


def _actual_direction(text: str, move: float) -> str:
    # Prefer an explicit word from the evidence. Use the sign only when the
    # table contains a number without an UP/DOWN label.
    lowered = text.lower()
    if "down" in lowered:
        return "DOWN"
    if "up" in lowered:
        return "UP"
    if abs(move) < FLAT_MOVE_THRESHOLD:
        return "FLAT"
    return "UP" if move > 0 else "DOWN"


def _table_cells(line: str) -> list[str]:
    cells: list[str] = []
    for cell in line.strip().strip("|").split("|"):
        cells.append(cell.strip())
    return cells


def _clean_markdown(text: str) -> str:
    return re.sub(r"[*_`]", "", text).strip()


def _has_number(text: str) -> bool:
    return re.search(r"[-+]?\d+(?:\.\d+)?", text) is not None


def _require_core_assets(rows: Mapping[str, object], label: str) -> None:
    missing: list[str] = []
    for asset in CORE_ASSETS:
        if asset not in rows:
            missing.append(asset)
    if missing:
        raise ValueError(f"Missing {label} rows for: {', '.join(missing)}")
