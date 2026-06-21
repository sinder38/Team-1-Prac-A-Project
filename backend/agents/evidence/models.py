"""Shared data objects and market lists for the evidence report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Final


EM_DASH: Final[str] = "\u2014"
PROJECT_WEEK_OFFSET: Final[int] = 20


@dataclass(frozen=True)
class MarketSpec:
    label: str
    short_name: str
    ticker: str
    close_kind: str


@dataclass(frozen=True)
class SectorSpec:
    name: str
    ticker: str
    description: str


@dataclass(frozen=True)
class MarketMove:
    spec: MarketSpec
    close: float | None
    weekly_change: float | None
    error: str | None = None


@dataclass(frozen=True)
class YieldMove:
    close: float | None
    weekly_change_points: float | None
    error: str | None = None


@dataclass(frozen=True)
class SectorMove:
    spec: SectorSpec
    weekly_change: float | None
    error: str | None = None


@dataclass(frozen=True)
class EvidenceSnapshot:
    prediction_date: date
    week_start: date
    week_end: date
    last_market_date: date
    open_days: int
    indexes: list[MarketMove]
    gold: MarketMove
    oil: MarketMove
    ten_year: YieldMove
    bonds: MarketMove
    vix: MarketMove
    bitcoin: MarketMove
    sectors: list[SectorMove]
    technical_chart_links: list[tuple[str, str]]


INDEX_SPECS: Final[list[MarketSpec]] = [
    MarketSpec("S&P 500 \u2014 large U.S. companies", "SPX", "^GSPC", "index"),
    MarketSpec("Nasdaq 100 \u2014 mostly tech", "NDX", "^NDX", "index"),
    MarketSpec("Russell 2000 \u2014 smaller companies", "IWM", "IWM", "etf"),
]

GOLD_SPEC: Final[MarketSpec] = MarketSpec("**Gold**", "Gold", "GC=F", "gold")
OIL_SPEC: Final[MarketSpec] = MarketSpec("**Oil** (U.S. crude)", "Oil", "CL=F", "oil")
BONDS_SPEC: Final[MarketSpec] = MarketSpec("**Bonds** (TLT fund)", "TLT", "TLT", "etf")
VIX_SPEC: Final[MarketSpec] = MarketSpec(
    "**VIX** (how scared traders are; lower = calmer)", "VIX", "^VIX", "vix"
)
BITCOIN_SPEC: Final[MarketSpec] = MarketSpec("**Bitcoin**", "Bitcoin", "BTC-USD", "bitcoin")

SECTOR_SPECS: Final[list[SectorSpec]] = [
    SectorSpec("Technology", "XLK", "software, chips, and hardware"),
    SectorSpec("Energy (oil & gas companies)", "XLE", "oil and gas producers"),
    SectorSpec("Financials (banks, insurance)", "XLF", "banks, brokers, and insurers"),
    SectorSpec(
        "Consumer discretionary (cars, hotels, shopping)",
        "XLY",
        "consumer spending-sensitive stocks",
    ),
    SectorSpec(
        "Consumer staples (food, toothpaste, etc.)",
        "XLP",
        "defensive food and household products",
    ),
    SectorSpec("Industrials", "XLI", "manufacturers, transport, and machinery"),
    SectorSpec(
        "Materials (chemicals, metals, etc.)",
        "XLB",
        "chemicals, metals, and industrial inputs",
    ),
    SectorSpec("Health care", "XLV", "health care and pharmaceuticals"),
    SectorSpec("Utilities (power, water)", "XLU", "regulated power and water utilities"),
    SectorSpec("Real estate", "XLRE", "property and REIT stocks"),
    SectorSpec(
        "Communication (phones, media, ads)",
        "XLC",
        "telecom, media, and internet platforms",
    ),
]