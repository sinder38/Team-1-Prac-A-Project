"""
Encoded next week major events data for the Macro Agent.

Added Confirmed news
"""

from dataclasses import dataclass


@dataclass
class Event:
    name: str
    impact: str  # HIGH, MEDIUM, LOW
    priority: int   # 0-100


UPCOMING_EVENTS = [
    Event(
        "US Fed Interest Rate Decision (18 Jun 2026, Thur 2:00 AM)",
        "HIGH",
        100
    ),
    Event(
        "FOMC Economic Projections (18 Jun 2026, Thur 2:00 AM)",
        "HIGH",
        95
    ),
    Event(
        "Fed Press Conference (18 Jun 2026, Thur 2:30 AM)",
        "HIGH",
        90
    ),
    Event(
        "BoE Interest Rate Decision (18 Jun 2026, Thur 7:00 PM)",
        "MEDIUM",
        70
    ),
]

CONFIRMED_NEWS = """
 · US stocks rise after oil prices ease and SpaceX soars in its debut on Wall Street — Source: AP — 13 Jun 2026
 · US and Iran have agreed to wording of a deal to end their war, Pakistan’s prime minister says — Source: AP — 13 Jun 2026
 · Iran peace deal looms while new military action flares near Strait of Hormuz — Source: Reuters, AP — 13 Jun 2026"""

