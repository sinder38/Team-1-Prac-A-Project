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
    next_fomc_date=date(2026, 7, 29),
    hold_probability=61.5,
    cut_probability=0,
    direction_vs_last_week="shifted hawkish",
)


UPCOMING_EVENTS = [
    Event(
        name="US Non-Farm Payrolls",
        date_label="Thursday, July 2",
        impact="HIGH",
        priority=100,
        expected="70K",
        previous="172K",
        catalyst_name="US Employment Report",
        catalyst_date="July 2",
    ),
    Event(
        name="US Unemployment Rate",
        date_label="Thursday, July 2",
        impact="HIGH",
        priority=95,
        expected="4.50%",
        previous="4.30%",
        catalyst_name="US Employment Report",
        catalyst_date="July 2",
    ),
    Event(
        name="US ISM Manufacturing PMI",
        date_label="Wednesday, July 1",
        impact="HIGH",
        priority=90,
        expected="52.5",
        previous="54.0",
        catalyst_name="US Manufacturing Activity",
        catalyst_date="July 1",
    ),
    Event(
        name="China NBS Manufacturing PMI",
        date_label="Tuesday, June 30",
        impact="HIGH",
        priority=85,
        expected="50.3",
        previous="50.0",
        catalyst_name="China Manufacturing PMI",
        catalyst_date="June 30",
    ),
    Event(
        name="Euro Area CPI Flash",
        date_label="Wednesday, July 1",
        impact="MEDIUM",
        priority=75,
        expected="3.2%",
        previous="3.2%",
        catalyst_name="Eurozone Inflation",
        catalyst_date="July 1",
    ),
]

KEY_EARNINGS = [
    "- FedEx Corp. (FDX) — Tuesday, June 23 (After Close) — Sector: Industrials / Transportation — What to watch: global shipping demand, freight volumes, economic activity indicators and FY outlook.",

    "- Paychex Inc. (PAYX) — Wednesday, June 24 (Before Open) — Sector: Financials / Payroll Services — What to watch: employment trends, SMB hiring activity and management commentary on labor markets.",

    "- Micron Technology Inc. (MU) — Wednesday, June 24 (After Close) — Sector: Technology / Semiconductors — What to watch: AI memory demand, HBM pricing, data center growth and FY guidance.",

    "- Trip.com Group Ltd. (TCOM) — Wednesday, June 24 (After Close) — Sector: Consumer Discretionary / Travel — What to watch: China travel demand, international bookings and consumer spending trends.",

    "- Darden Restaurants Inc. (DRI) — Thursday, June 25 (Before Open) — Sector: Consumer Discretionary / Restaurants — What to watch: same-store sales, consumer spending trends and forward guidance.",
]

CONFIRMED_NEWS = [
    "- US Vice President JD Vance met senior Iranian officials in Switzerland as Washington seeks to restart negotiations and reduce regional tensions — Source: AP — 21 Jun 2026",

    "- President Trump threatened additional military strikes against Iran while diplomatic talks continue, increasing geopolitical uncertainty in the Middle East — Source: Reuters — 21 Jun 2026",

    "- Markets continue monitoring developments around Iran, the Strait of Hormuz and global energy supply risks as diplomatic and military signals remain mixed — Source: Reuters, AP — 21 Jun 2026",
]