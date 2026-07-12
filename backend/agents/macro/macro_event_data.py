"""Source URLs and shared data structures for the Macro Agent."""
from dataclasses import dataclass
from datetime import date

TRADING_ECONOMICS_CALENDAR_URL = "https://tradingeconomics.com/calendar"
TRADING_ECONOMICS_EARNINGS_URL = "https://tradingeconomics.com/earnings"
EARNINGS_WHISPERS_CALENDAR_URL = "https://www.earningswhispers.com/calendar/"
NEWSDATA_LATEST_URL = "https://newsdata.io/api/1/latest"


@dataclass
class Event:
    name: str
    date_label: str
    impact: str  # HIGH, MEDIUM, LOW
    priority: int   # 0-100
    event_date: date | None = None
    expected: str = "N/A"
    previous: str = "N/A"
    catalyst_name: str = ""
    catalyst_date: str = ""
    source_url: str = TRADING_ECONOMICS_CALENDAR_URL


@dataclass
class NewsItem:
    headline: str
    source: str
    section: str
    url: str
    score: int
    impact: str
    published_label: str = ""


@dataclass
class EarningsEvent:
    company: str
    ticker: str
    date_label: str
    timing: str
    sector: str
    priority: int
    impact: str
    watch: str
    source_url: str = EARNINGS_WHISPERS_CALENDAR_URL


@dataclass
class FomcMarketPricing:
    next_fomc_date: date | None
    hold_probability: float
    cut_probability: float
    direction_vs_last_week: str