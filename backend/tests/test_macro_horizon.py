"""Tests for Macro TradingEconomics horizon window + month/importance cookies."""

from datetime import date, timedelta
from inspect import signature

from agents.macro.macro_event_data import TRADING_ECONOMICS_CALENDAR_URL
from agents.macro.macro_sources import (
    EarningsWhispersCalendar,
    SourceFetcher,
    TradingEconomicsCalendar,
    forward_window,
    next_week_window,
)


class FakeFetcher(SourceFetcher):
    """Records fetch_text calls and returns configured HTML (no network)."""

    def __init__(self, html: str = "") -> None:
        self.html = html
        self.calls: list[tuple[str, dict]] = []

    def fetch_text(self, url: str, cookies: dict | None = None) -> str:
        self.calls.append((url, cookies or {}))
        return self.html


def _tradingeconomics_row(
    event_date: date,
    name: str,
    *,
    country: str = "united states",
    path: str = "/united-states/interest-rate",
    rank: int = 3,
) -> str:
    """Minimal TE calendar row that parse_events / _parse_event_row accept."""
    return f"""
<tr data-url="{path}" data-country="{country}">
  <span class="calendar-date-{rank} {event_date.isoformat()}">2:00 PM</span>
  <a class="calendar-event" href="{path}">{name}</a>
  <span id="previous">N/A</span>
  <span id="consensus">N/A</span>
</tr>
"""


def test_forward_window_week_default():
    d = date(2026, 6, 18)
    assert forward_window(d, 7) == next_week_window(d)


def test_forward_window_longer():
    d = date(2026, 6, 18)
    start, end = forward_window(d, 14)
    assert start == d + timedelta(days=1)
    assert end == d + timedelta(days=14)


def test_get_top_events_fetches_this_and_next_month_with_3star():
    fetcher = FakeFetcher()
    cal = TradingEconomicsCalendar(fetcher=fetcher)
    cal.get_top_events(date(2026, 6, 18), horizon_days=14)

    assert len(fetcher.calls) == 2
    assert fetcher.calls[0][1] == {
        "calendar-range": "5",
        "calendar-importance": "3",
    }
    assert fetcher.calls[1][1] == {
        "calendar-range": "6",
        "calendar-importance": "3",
    }
    assert all(url == TRADING_ECONOMICS_CALENDAR_URL for url, _ in fetcher.calls)


def test_parse_events_respects_horizon_window():
    prediction_date = date(2026, 6, 18)
    start, end = forward_window(prediction_date, 14)
    html = (
        _tradingeconomics_row(
            date(2026, 6, 24),
            "CPI",
            path="/united-states/inflation-cpi",
        )
        + _tradingeconomics_row(
            date(2026, 7, 20),
            "Fed Interest Rate Decision",
            path="/united-states/interest-rate",
        )
    )

    # parse_events does not call the fetcher
    cal = TradingEconomicsCalendar(fetcher=FakeFetcher())
    events = cal.parse_events(html, start, end)

    dates = {e.event_date for e in events}
    assert date(2026, 6, 24) in dates
    assert date(2026, 7, 20) not in dates
    assert len(events) == 1


def test_get_top_events_filters_by_horizon():
    """Same HTML pool; longer horizon can keep the farther event."""
    near = date(2026, 6, 24)  # inside next-week window for 2026-06-18
    far = date(2026, 7, 1)  # outside week; inside 14-day forward_window

    html = (
        _tradingeconomics_row(
            near,
            "CPI",
            path="/united-states/inflation-cpi",
        )
        + _tradingeconomics_row(
            far,
            "Fed Interest Rate Decision",
            path="/united-states/interest-rate",
        )
    )

    # Both month fetches return the same fixture HTML
    cal = TradingEconomicsCalendar(fetcher=FakeFetcher(html=html))
    prediction_date = date(2026, 6, 18)

    short = cal.get_top_events(prediction_date, limit=5, horizon_days=7)
    long = cal.get_top_events(prediction_date, limit=5, horizon_days=14)

    short_dates = {e.event_date for e in short}
    long_dates = {e.event_date for e in long}

    assert near in short_dates
    assert far not in short_dates
    assert near in long_dates
    assert far in long_dates


def test_earnings_whispers_still_week_only():
    d = date(2026, 6, 18)
    week_start, week_end = next_week_window(d)

    urls = EarningsWhispersCalendar.earningswhispers_daily_urls(d)
    assert urls, "expected daily EW URLs for the next week"
    assert urls[0][0] == week_start
    assert urls[-1][0] == week_end

    params = signature(EarningsWhispersCalendar.get_key_events).parameters
    assert "horizon_days" not in params

    for event_date, _url in urls:
        assert week_start <= event_date <= week_end
