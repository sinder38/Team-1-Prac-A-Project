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
    hold_probability=78.1,
    cut_probability=0,
    direction_vs_last_week="shifted dovish",
)


UPCOMING_EVENTS = [
    Event(
        name="US ISM Services PMI",
        date_label="Monday, July 6",
        impact="HIGH",
        priority=100,
        expected="54.2",
        previous="54.5",
        catalyst_name="US Services Activity",
        catalyst_date="July 6",
    ),
    Event(
        name="FOMC Minutes",
        date_label="Thursday, July 9",
        impact="HIGH",
        priority=95,
        expected="N/A",
        previous="N/A",
        catalyst_name="Federal Reserve Minutes",
        catalyst_date="July 9",
    ),
    Event(
        name="China Inflation Rate YoY",
        date_label="Thursday, July 9",
        impact="Medium",
        priority=85,
        expected="1.2%",
        previous="1.2%",
        catalyst_name="China Inflation",
        catalyst_date="July 9",
    ),
    Event(
        name="US Existing Home Sales",
        date_label="Thursday, July 9",
        impact="MEDIUM",
        priority=75,
        expected="4.20M",
        previous="4.17M",
        catalyst_name="US Housing Market",
        catalyst_date="July 9",
    ),
    Event(
        name="Canada Unemployment Rate",
        date_label="Friday, July 10",
        impact="MEDIUM",
        priority=65,
        expected="6.6%",
        previous="6.6%",
        catalyst_name="Canada Employment Report",
        catalyst_date="July 10",
    ),
]

KEY_EARNINGS = [
    "- PepsiCo, Inc. (PEP) — Thursday, July 9 (Before Open) — Sector: Consumer Staples / Food & Beverages — What to watch: consumer demand, pricing power, snack and beverage volumes, margin trends and FY guidance.",

    "- Delta Air Lines, Inc. (DAL) — Friday, July 10 (Before Open) — Sector: Industrials / Airlines — What to watch: domestic and international travel demand, corporate bookings, fuel costs and full-year outlook.",

    "- Levi Strauss & Co. (LEVI) — Wednesday, July 8 (After Close) — Sector: Consumer Discretionary / Apparel — What to watch: consumer spending, inventory levels, wholesale demand, DTC sales and tariff commentary.",

    "- Penguin Solutions, Inc. (PENG) — Tuesday, July 7 (After Close) — Sector: Technology / Enterprise Infrastructure — What to watch: AI infrastructure demand, enterprise spending, storage and memory solutions growth and guidance.",

    "- Kura Sushi USA, Inc. (KRUS) — Tuesday, July 7 (After Close) — Sector: Consumer Discretionary / Restaurants — What to watch: same-store sales, restaurant traffic, consumer spending trends and expansion plans.",
]

CONFIRMED_NEWS = [
    "- U.S. oil companies are expected to report their strongest quarterly profits in years, potentially setting up a clash with President Trump over gasoline prices ahead of the November midterm elections — Source: Reuters — 4 Jul 2026",

    "- Iran is exploring the resumption of crude oil sales to Japan as buyers seek a longer U.S. sanctions waiver, highlighting ongoing uncertainty around global energy supplies — Source: Reuters — 4 Jul 2026",

    "- Reuters analysis found the recent U.S.-Iran conflict has resulted in significantly smaller oil supply disruptions than the 1979 oil shock, easing fears of a prolonged energy crisis — Source: Reuters — 4 Jul 2026",
]
