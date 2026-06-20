"""
Encoded next week major events data for the Macro Agent.
Added Confirmed news
Added Key Earnings
"""
from dataclasses import dataclass
from datetime import date


@dataclass
class Event:
    name: str
    date_label: str
    impact: str  # HIGH, MEDIUM, LOW
    priority: int   # 0-100
    expected: str = "N/A"
    previous: str = "N/A"
    catalyst_name: str = ""
    catalyst_date: str = ""


@dataclass
class FomcMarketPricing:
    next_fomc_date: date
    hold_probability: float
    cut_probability: float
    direction_vs_last_week: str


FOMC_MARKET_PRICING = FomcMarketPricing(
    next_fomc_date=date(2026, 6, 18),
    hold_probability=97.4,
    cut_probability=2.6,
    direction_vs_last_week="shifted hawkish slightly",
)


UPCOMING_EVENTS = [
    Event(
        name="US Fed Interest Rate Decision",
        date_label="Thursday, June 18",
        impact="HIGH",
        priority=100,
        expected="Hold",
        previous="3.50%-3.75%",
        catalyst_name="US Fed Interest Rate Decision",
        catalyst_date="June 18",
    ),
    Event(
        name="FOMC Economic Projections",
        date_label="Thursday, June 18",
        impact="HIGH",
        priority=95,
        catalyst_name="FOMC Economic Projections",
        catalyst_date="June 18",
    ),
    Event(
        name="Fed Press Conference",
        date_label="Thursday, June 18",
        impact="HIGH",
        priority=90,
        catalyst_name="Fed Press Conference",
        catalyst_date="June 18",
    ),
    Event(
        name="BoE Interest Rate Decision",
        date_label="Thursday, June 18",
        impact="MEDIUM",
        priority=70,
        expected="3.75%",
        previous="3.75%",
        catalyst_name="BoE Interest Rate Decision",
        catalyst_date="June 18",
    ),
]

KEY_EARNINGS = [
    "- Accenture Ltd. (ACN) — Thursday, June 18 (Before Open) — Sector: XLK/XLF (Enterprise Tech / Consulting) — What to watch: enterprise IT spending, AI-related transformation budgets, broader software and tech sentiment.",
    "- Progressive Corp. (PGR) — Wednesday, June 17 (Before Open) — Sector: XLF (Financials) — What to watch: Insurance margin strength and pricing trends",
    "- Jabil Inc. (JBL) — Wednesday, June 17 (Before Open) — Sector: XLK (Tech Hardware / AI Supply Chain) — What to watch: electronics demand and AI infrastructure supply chain momentum."
]

CONFIRMED_NEWS = [
    "- US stocks rise after oil prices ease and SpaceX soars in its debut on Wall Street — Source: AP — 13 Jun 2026",
    "- US and Iran have agreed to wording of a deal to end their war, Pakistan's prime minister says — Source: AP — 13 Jun 2026",
    "- Iran peace deal looms while new military action flares near Strait of Hormuz — Source: Reuters, AP — 13 Jun 2026",
]
