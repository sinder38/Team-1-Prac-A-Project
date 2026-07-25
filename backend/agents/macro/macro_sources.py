"""Source collectors used by the Macro Agent."""

import html
import os
import re
from datetime import date, timedelta
from urllib.parse import urljoin, urlparse

import requests

from agents.macro.macro_event_data import (
    EARNINGS_WHISPERS_CALENDAR_URL,
    NEWSDATA_LATEST_URL,
    TRADING_ECONOMICS_CALENDAR_URL,
    TRADING_ECONOMICS_EARNINGS_URL,
    EarningsEvent,
    Event,
    FomcMarketPricing,
    NewsItem,
)

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; MarketMacroAgent/1.0; "
        "+https://github.com/market-prediction)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

COUNTRY_RELEVANCE = {
    "united states": 16,
    "euro area": 9,
    "china": 9,
    "japan": 6,
    "united kingdom": 6,
    "germany": 5,
    "canada": 3,
}

EVENT_TYPE_WEIGHTS = [
    (("interest rate", "fomc", "fed press", "powell"), 28),
    (("core pce", "pce price", "cpi", "inflation"), 22),
    (("gdp", "growth rate"), 18),
    (("pmi", "ism", "durable goods"), 14),
    (("non farm", "payroll", "jobless", "claims", "unemployment"), 17),
    (("consumer sentiment", "consumer confidence", "michigan"), 10),
    (("crude oil", "gasoline", "eia", "api"), 9),
    (("retail sales", "personal spending", "personal income"), 8),
    (("auction", "bond", "bill"), -10),
]

EVENT_GROUPS = [
    (("core pce", "pce price", "pce prices"), "pce"),
    (("gdp growth", "gdp price", "gdp sales", "real consumer spending"), "gdp"),
    (("durable goods", "non defense goods"), "durable-goods"),
    (("personal income", "personal spending"), "personal-income-spending"),
    (("s&p global", "pmi"), "pmi"),
    (("michigan",), "michigan-sentiment"),
    (("jobless claims",), "jobless-claims"),
    (("eia", "api crude", "crude oil stocks"), "energy-inventory"),
    (("interest rate", "fomc", "fed press"), "fed"),
]

NEWS_KEYWORD_WEIGHTS = [
    (("iran", "israel", "war", "hormuz"), 20),
    (("oil", "crude", "opec", "energy"), 14),
    (("stocks", "markets", "rates", "treasury", "dollar"), 12),
    (("fed", "inflation", "cpi", "jobs", "earnings"), 10),
    (("deal", "ceasefire", "sanctions", "exports"), 9),
    (("business", "economy", "trade", "tariff"), 8),
    (("ai", "nvidia", "semiconductor"), 6),
]

NEWSDATA_QUERIES = [
    ("Iran OR Israel OR Hormuz OR oil", "Geopolitical / energy risk"),
    ("stocks OR markets OR Fed OR inflation OR earnings", "Markets / macro"),
    ("business OR economy OR tariff OR semiconductor OR AI", "Business / sectors"),
]

CONFIRMED_NEWS_DOMAINS = (
    "reuters.com",
    "apnews.com",
)

EARNINGS_KEYWORD_WEIGHTS = [
    (("micron", "mu", "semiconductor", "technology", "xlk"), 35),
    (("fedex", "fdx", "transport", "industrial", "xli"), 32),
    (("carnival", "ccl", "travel", "consumer", "xly"), 26),
    (("paychex", "payx", "payroll", "business services"), 22),
    (("darden", "restaurant", "retail"), 20),
    (("financial", "bank", "insurance"), 18),
    (("healthcare", "energy"), 16),
]

SECTOR_HINTS = [
    (("pep", "pepsico", "wd-40", "seven", "aeon"), "XLP / Consumer Staples"),
    (("delta", "air lines", "hyatt", "jets", "travel", "netflix", "nflx"), "XLY / Travel & Leisure"),
    (("jpmorgan", "jpm", "bank of america", "bac", "bank", "progressive", "washington federal", "insurance"), "XLF / Financials"),
    (("j&j", "johnson", "unitedhealth", "unh", "health"), "XLV / Healthcare"),
    (("tata consultancy", "technology", "semiconductor", "software"), "XLK / Technology"),
    (("cintas", "msc industrial", "enerpac", "yaskawa"), "XLI / Industrials"),
    (("aritzia", "pricesmart", "retail"), "XLY / Retail"),
]


def next_week_window(prediction_date: date) -> tuple[date, date]:
    """Return the Monday-Friday window after the prediction date's week."""
    days_until_next_monday = 7 - prediction_date.weekday()
    start = prediction_date + timedelta(days=days_until_next_monday)
    return start, start + timedelta(days=4)


def clean_html(value: str) -> str:
    """Remove tags/entities and normalize whitespace."""
    without_tags = re.sub(r"<[^>]+>", " ", value)
    return html.unescape(re.sub(r"\s+", " ", without_tags)).strip()


def clamp_score(score: int) -> int:
    """Keep scores in the report-friendly 0-100 range."""
    return max(0, min(100, score))


def apply_keyword_weights(text: str, weights: list[tuple[tuple[str, ...], int]]) -> int:
    """Return the sum of all matching keyword weights."""
    text = text.lower()
    return sum(
        weight
        for keywords, weight in weights
        if any(keyword in text for keyword in keywords)
    )


class SourceFetcher:
    """Tiny wrapper around requests so source collectors are easy to test."""

    def fetch_text(self, url: str) -> str:
        response = requests.get(url, headers=HTTP_HEADERS, timeout=20)
        response.raise_for_status()
        return response.text

    def fetch_json(self, url: str, params: dict) -> dict:
        response = requests.get(url, params=params, headers=HTTP_HEADERS, timeout=20)
        response.raise_for_status()
        return response.json()


class TradingEconomicsCalendar:
    """Fetch, parse, and rank next-week TradingEconomics calendar events."""

    def __init__(self, fetcher: SourceFetcher | None = None):
        self.fetcher = fetcher or SourceFetcher()

    def get_top_events(self, prediction_date: date, limit: int = 5) -> list[Event]:
        """Return the top next-week events from TradingEconomics."""
        start_date, end_date = next_week_window(prediction_date)
        try:
            html_text = self.fetcher.fetch_text(TRADING_ECONOMICS_CALENDAR_URL)
            events = self.parse_events(html_text, start_date, end_date)
            selected = self.select_top_events(events, limit)
            if selected:
                return selected
        except (requests.RequestException, ValueError, AttributeError) as exc:
            print(f"Warning: TradingEconomics calendar unavailable ({exc}); continuing.")

        return []

    def parse_events(
            self,
            html_text: str,
            start_date: date,
            end_date: date,
    ) -> list[Event]:
        """Parse TradingEconomics calendar rows inside a date window."""
        events: list[Event] = []
        for raw_chunk in html_text.split("<tr data-url=")[1:]:
            event = self._parse_event_row("<tr data-url=" + raw_chunk)
            if event and event.event_date and start_date <= event.event_date <= end_date:
                events.append(event)
        return events

    def select_top_events(self, events: list[Event], limit: int = 5) -> list[Event]:
        """Prefer US events for US-index forecasts, then dedupe related rows."""
        us_events = [event for event in events if "/united-states/" in event.source_url]
        candidate_events = us_events if len(us_events) >= limit else events

        grouped_events = self._best_event_per_group(candidate_events)
        selected = sorted(
            grouped_events,
            key=lambda event: (
                event.priority,
                event.impact == "HIGH",
                event.event_date or date.min,
            ),
            reverse=True,
        )[:limit]
        return self._with_distinct_priorities(selected)

    def _parse_event_row(self, chunk: str) -> Event | None:
        event_date = self._row_date(chunk)
        event_name = self._row_event_name(chunk)
        if event_date is None or not event_name:
            return None

        source_impact = self._impact_from_calendar_rank(chunk)
        country = self._attribute(chunk, "data-country")
        source_path = self._attribute(chunk, "data-url")
        priority = self._priority(event_name, country, source_impact)

        return Event(
            name=self._display_name(country, event_name),
            date_label=self._date_label(event_date, self._row_time(chunk)),
            impact=self._impact(priority, source_impact),
            priority=priority,
            event_date=event_date,
            expected=self._expected_value(chunk),
            previous=self._id_value(chunk, "previous") or "N/A",
            catalyst_name=event_name,
            catalyst_date=f"{event_date.strftime('%B')} {event_date.day}",
            source_url=urljoin(TRADING_ECONOMICS_CALENDAR_URL, source_path),
        )

    @staticmethod
    def _attribute(chunk: str, attr: str) -> str:
        match = re.search(rf"{attr}=(['\"])(.*?)\1", chunk, flags=re.IGNORECASE | re.DOTALL)
        return html.unescape(match.group(2)).strip() if match else ""

    @staticmethod
    def _id_value(chunk: str, field_id: str) -> str:
        pattern = rf"id=['\"]{field_id}['\"][^>]*>(.*?)</(?:span|a)>"
        match = re.search(pattern, chunk, flags=re.IGNORECASE | re.DOTALL)
        return clean_html(match.group(1)) if match else ""

    @staticmethod
    def _row_date(chunk: str) -> date | None:
        match = re.search(r"class=['\"][^'\"]*(\d{4}-\d{2}-\d{2})", chunk)
        return date.fromisoformat(match.group(1)) if match else None

    @staticmethod
    def _row_event_name(chunk: str) -> str:
        event_match = re.search(
            r"class=['\"]calendar-event['\"][^>]*>(.*?)</a>",
            chunk,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not event_match:
            return ""

        name = clean_html(event_match.group(1))
        reference_match = re.search(
            r"class=['\"]calendar-reference['\"][^>]*>(.*?)</span>",
            chunk,
            flags=re.IGNORECASE | re.DOTALL,
        )
        reference = clean_html(reference_match.group(1)) if reference_match else ""
        return f"{name} {reference}" if reference and reference not in name else name

    @staticmethod
    def _row_time(chunk: str) -> str:
        match = re.search(
            r"class=['\"][^'\"]*calendar-date-\d+['\"][^>]*>(.*?)</span>",
            chunk,
            flags=re.IGNORECASE | re.DOTALL,
        )
        return clean_html(match.group(1)) if match else ""

    @staticmethod
    def _impact_from_calendar_rank(chunk: str) -> str:
        match = re.search(r"calendar-date-(\d+)", chunk)
        rank = int(match.group(1)) if match else 1
        if rank >= 3:
            return "HIGH"
        if rank == 2:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _priority(name: str, country: str, source_impact: str) -> int:
        score = {"HIGH": 45, "MEDIUM": 30, "LOW": 15}.get(source_impact.upper(), 15)
        score += COUNTRY_RELEVANCE.get(country.lower(), 0)
        score += apply_keyword_weights(f"{country} {name}", EVENT_TYPE_WEIGHTS)
        return clamp_score(score)

    @staticmethod
    def _impact(priority: int, source_impact: str) -> str:
        if priority >= 78 or (source_impact.upper() == "HIGH"):
            return "HIGH"
        if priority >= 58 or source_impact.upper() in {"HIGH", "MEDIUM"}:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _expected_value(chunk: str) -> str:
        return (
            TradingEconomicsCalendar._id_value(chunk, "consensus")
            or TradingEconomicsCalendar._id_value(chunk, "forecast")
            or "N/A"
        )

    @staticmethod
    def _display_name(country: str, name: str) -> str:
        if country.lower() == "united states":
            return f"US {name}"
        if country:
            return f"{country.title()} {name}"
        return name

    @staticmethod
    def _date_label(event_date: date, event_time: str) -> str:
        label = f"{event_date.strftime('%A, %B')} {event_date.day}"
        return f"{label}, {event_time}" if event_time else label

    @staticmethod
    def _best_event_per_group(events: list[Event]) -> list[Event]:
        grouped: dict[str, Event] = {}
        for event in events:
            key = TradingEconomicsCalendar._group_key(event)
            if key not in grouped or event.priority > grouped[key].priority:
                grouped[key] = event
        return list(grouped.values())

    @staticmethod
    def _with_distinct_priorities(events: list[Event]) -> list[Event]:
        """Avoid identical top-five priorities in the human report."""
        previous_priority = 101
        for event in events:
            adjusted = min(event.priority, previous_priority - 1)
            event.priority = max(adjusted, 1)
            previous_priority = event.priority
        return events

    @staticmethod
    def _group_key(event: Event) -> str:
        name = event.name.lower()
        country_prefix = ""
        if "united-states" in event.source_url:
            country_prefix = "us:"
        elif "euro-area" in event.source_url:
            country_prefix = "euro:"

        for keywords, group_name in EVENT_GROUPS:
            if any(keyword in name for keyword in keywords):
                return f"{country_prefix}{group_name}"
        return f"{country_prefix}{name}"


class ConfirmedNewsSource:
    """Fetch and rank market-relevant headlines from Reuters and Apnews through NewsData.io."""

    def __init__(self, fetcher: SourceFetcher | None = None, api_key: str | None = None):
        self.fetcher = fetcher or SourceFetcher()
        self.api_key = api_key or os.getenv("NEWSDATA_API_KEY") or os.getenv("NEWS_DATA_API_KEY")

    def get_ranked_items(self, limit: int = 5) -> list[NewsItem]:
        if not self.api_key:
            print("Warning: NEWSDATA_API_KEY is not set; confirmed news will be empty.")
            return []

        items = self._fetch_newsdata_items()
        ranked = sorted(self._dedupe_by_url_or_headline(items), key=lambda item: item.score, reverse=True)
        return self.select_diverse_items(ranked, limit)

    def parse_newsdata_results(self, payload: dict, section: str) -> list[NewsItem]:
        """Convert NewsData.io latest endpoint results to scored NewsItem rows."""
        items: list[NewsItem] = []
        for article in payload.get("results") or []:
            title = clean_html(article.get("title") or "")
            link = article.get("link") or ""
            if not title or not link:
                continue
            if not self._is_allowed_confirmed_source(article):
                continue

            description = clean_html(article.get("description") or "")

            source_name = article.get("source_name") or "NewsData.io(reuters or apnews)"
            score = self.score_headline(f"{title} {description}", section)
            if score < 60:
                continue

            items.append(
                NewsItem(
                    headline=title,
                    source=source_name,
                    section=section,
                    url=link,
                    score=score,
                    impact=self.impact_from_score(score),
                    published_label=article.get("pubDate") or "",
                )
            )

        return items

    @staticmethod
    def score_headline(headline: str, section: str) -> int:
        score = 35
        section_lower = section.lower()
        if "geopolitical" in section_lower:
            score += 8
        elif "business" in section_lower or "markets" in section_lower:
            score += 5
        score += apply_keyword_weights(headline, NEWS_KEYWORD_WEIGHTS)
        return clamp_score(score)

    @staticmethod
    def impact_from_score(score: int) -> str:
        if score >= 80:
            return "HIGH"
        if score >= 60:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def render_item(item: NewsItem) -> str:
        published = f" — {item.published_label}" if item.published_label else ""
        return (
            f"- [{item.headline}]({item.url}) — Source: {item.source} "
            f"({item.section}){published} — IMPORTANCE: {item.impact.title()} "
            f"— Score: {item.score}/100"
        )

    def _fetch_newsdata_items(self) -> list[NewsItem]:
        items: list[NewsItem] = []
        for query, section in NEWSDATA_QUERIES:
            try:
                payload = self.fetcher.fetch_json(
                    NEWSDATA_LATEST_URL,
                    {
                        "apikey": self.api_key,
                        "q": query,
                        "language": "en",
                        "domainurl": ",".join(CONFIRMED_NEWS_DOMAINS),
                    },
                )
            except requests.RequestException as exc:
                print(f"Warning: NewsData.io {section} news unavailable ({exc}); continuing.")
                continue
            if payload.get("status") == "error":
                print(
                    "Warning: NewsData.io returned an error for "
                    f"{section}: {payload.get('message') or payload.get('results')}"
                )
                continue
            items.extend(self.parse_newsdata_results(payload, section))
        return items

    @staticmethod
    def _dedupe_by_url_or_headline(items: list[NewsItem]) -> list[NewsItem]:
        deduped: dict[str, NewsItem] = {}
        for item in items:
            key = item.url or item.headline.lower()
            if key not in deduped or item.score > deduped[key].score:
                deduped[key] = item
        return list(deduped.values())

    @staticmethod
    def select_diverse_items(items: list[NewsItem], limit: int = 5) -> list[NewsItem]:
        """Pick best items while keeping query-topic representation."""
        selected: list[NewsItem] = []

        for _query, section in NEWSDATA_QUERIES:
            match = next(
                (
                    item
                    for item in items
                    if item.section == section and item not in selected
                ),
                None,
            )
            if match:
                selected.append(match)

        for item in items:
            if len(selected) >= limit:
                break
            if item not in selected:
                selected.append(item)

        return selected[:limit]

    @staticmethod
    def _is_allowed_confirmed_source(article: dict) -> bool:
        source_text = " ".join(
            str(article.get(field) or "")
            for field in ("source_id", "source_name", "source_url")
        ).lower()
        source_words = set(re.findall(r"[a-z]+", source_text))
        if "reuters" in source_text or "associated press" in source_text or "ap news" in source_text:
            return True
        if "ap" in source_words:
            return True

        host = urlparse(article.get("link") or "").netloc.lower()
        return any(host == domain or host.endswith(f".{domain}") for domain in CONFIRMED_NEWS_DOMAINS)


class EarningsWhispersCalendar:
    """Fetch and rank key earnings from public earnings calendars."""

    def __init__(self, fetcher: SourceFetcher | None = None):
        self.fetcher = fetcher or SourceFetcher()

    def get_key_events(self, prediction_date: date, limit: int = 3) -> list[EarningsEvent]:
        """Prefer Earnings Whispers rows, then use TradingEconomics earnings."""
        events = self._fetch_earningswhispers_daily_events(prediction_date)
        if events:
            return events[:limit]

        try:
            start_date, end_date = next_week_window(prediction_date)
            html_text = self.fetcher.fetch_text(TRADING_ECONOMICS_EARNINGS_URL)
            events = self.parse_tradingeconomics_events(html_text, start_date, end_date)
            if events:
                return self._select_key_earnings(events, limit)
        except (requests.RequestException, ValueError, AttributeError) as exc:
            print(f"Warning: TradingEconomics earnings unavailable ({exc}); continuing.")

        return []

    def parse_events(self, html_text: str) -> list[EarningsEvent]:
        """Parse public stock links if Earnings Whispers exposes them."""
        events: list[EarningsEvent] = []
        for match in re.finditer(
                r"<a[^>]+href=(['\"])(?P<href>/stocks/(?P<ticker>[a-z0-9.-]+))\1[^>]*>(?P<body>.*?)</a>",
                html_text,
                flags=re.IGNORECASE | re.DOTALL,
        ):
            ticker = match.group("ticker").upper()
            company = clean_html(match.group("body")) or ticker
            score = self.score_event(company, ticker, "")
            events.append(
                EarningsEvent(
                    company=company,
                    ticker=ticker,
                    date_label="Monday-Friday",
                    timing="See source",
                    sector="Unclassified",
                    priority=score,
                    impact=ConfirmedNewsSource.impact_from_score(score),
                    watch="Earnings Whispers public calendar item.",
                    source_url=urljoin(EARNINGS_WHISPERS_CALENDAR_URL, match.group("href")),
                )
            )
        return events

    def parse_tradingeconomics_events(
            self,
            html_text: str,
            start_date: date,
            end_date: date,
    ) -> list[EarningsEvent]:
        """Parse TradingEconomics earnings rows inside a date window."""
        events: list[EarningsEvent] = []
        current_date: date | None = None
        current_label = ""

        for raw_chunk in html_text.split("<tr")[1:]:
            chunk = "<tr" + raw_chunk
            date_match = re.search(r'data-date-header="(\d{4}-\d{2}-\d{2})"', chunk)
            if date_match:
                current_date = date.fromisoformat(date_match.group(1))
                current_label = self._date_label(current_date)
                continue

            if current_date is None or not start_date <= current_date <= end_date:
                continue

            event = self._parse_tradingeconomics_row(chunk, current_label)
            if event:
                events.append(event)

        return events

    @staticmethod
    def score_event(company: str, ticker: str, sector: str) -> int:
        text = f"{company} {ticker} {sector}"
        return clamp_score(45 + apply_keyword_weights(text, EARNINGS_KEYWORD_WEIGHTS))

    @staticmethod
    def render_event(event: EarningsEvent) -> str:
        return (
            f"- [{event.company} ({event.ticker})]({event.source_url}) — "
            f"{event.date_label} ({event.timing}) — Sector: {event.sector} — "
            f"What to watch: {event.watch}"
        )

    @staticmethod
    def earningswhispers_daily_urls(prediction_date: date) -> list[tuple[date, str]]:
        start_date, end_date = next_week_window(prediction_date)
        days = (end_date - start_date).days + 1
        return [
            (
                start_date + timedelta(days=offset),
                f"{EARNINGS_WHISPERS_CALENDAR_URL}"
                f"{(start_date + timedelta(days=offset)).strftime('%Y%m%d')}/{session}",
            )
            for offset in range(days)
            for session in (1, 3)
        ]

    def _fetch_earningswhispers_daily_events(self, prediction_date: date) -> list[EarningsEvent]:
        events: list[EarningsEvent] = []
        for event_date, url in self.earningswhispers_daily_urls(prediction_date):
            try:
                html_text = self.fetcher.fetch_text(url)
            except requests.RequestException as exc:
                print(f"Warning: Earnings Whispers daily calendar unavailable for {event_date}: {exc}")
                continue
            for event in self.parse_events(html_text):
                event.date_label = self._date_label(event_date)
                if event.source_url == EARNINGS_WHISPERS_CALENDAR_URL:
                    event.source_url = url
                events.append(event)
        return events

    def _parse_tradingeconomics_row(self, chunk: str, date_label: str) -> EarningsEvent | None:
        symbol_match = re.search(
            r'<span class="earnings-symbol">(?P<symbol>[^<]+)</span>',
            chunk,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not symbol_match:
            return None

        link_match = re.search(
            r'<a[^>]+href="(?P<href>https://tradingeconomics.com/[^"]+:eps)"[^>]*>(?P<company>[^<]+)</a>\s*'
            r'<span class="earnings-symbol">',
            chunk,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not link_match:
            return None

        cells = [
            clean_html(cell)
            for cell in re.findall(r"<td[^>]*>(.*?)</td>", chunk, flags=re.IGNORECASE | re.DOTALL)
        ]
        if len(cells) < 8:
            return None

        company = clean_html(link_match.group("company"))
        symbol = clean_html(symbol_match.group("symbol"))
        ticker = symbol.split(":")[0]
        country_suffix = symbol.split(":")[-1] if ":" in symbol else ""
        market_cap = cells[5]
        fiscal_period = cells[6] or "N/A"
        timing = self._timing_label(cells[7])
        impact = self._tradingeconomics_impact(chunk)
        sector = self._sector_hint(company, ticker)
        priority = self._earnings_priority(company, ticker, sector, market_cap, impact)
        eps_consensus = self._consensus_value(cells[1])
        revenue_consensus = self._consensus_value(cells[3])

        return EarningsEvent(
            company=company,
            ticker=ticker,
            date_label=date_label,
            timing=timing,
            sector=sector,
            priority=priority,
            impact=impact,
            watch=(
                f"Market cap: {market_cap}; fiscal: {fiscal_period}; EPS consensus: {eps_consensus}; "
                f"revenue consensus: {revenue_consensus}; listing: {country_suffix.upper() or 'N/A'}."
            ),
            source_url=link_match.group("href"),
        )

    @staticmethod
    def _date_label(value: date) -> str:
        return f"{value.strftime('%A, %B')} {value.day}"

    @staticmethod
    def _timing_label(value: str) -> str:
        return {"AM": "Before Open", "PM": "After Close"}.get(value.strip().upper(), value or "N/A")

    @staticmethod
    def _tradingeconomics_impact(chunk: str) -> str:
        match = re.search(r'title="(High|Medium|Low) Market Impact"', chunk, flags=re.IGNORECASE)
        return match.group(1).upper() if match else "LOW"

    @staticmethod
    def _consensus_value(cell_text: str) -> str:
        if "/" in cell_text:
            return cell_text.split("/")[-1].strip() or "N/A"
        return cell_text or "N/A"

    @staticmethod
    def _sector_hint(company: str, ticker: str) -> str:
        text = f"{company} {ticker}".lower()
        for keywords, sector in SECTOR_HINTS:
            if any(keyword in text for keyword in keywords):
                return sector
        return "Cross-sector / source does not provide sector"

    @staticmethod
    def _earnings_priority(
            company: str,
            ticker: str,
            sector: str,
            market_cap: str,
            impact: str,
    ) -> int:
        score = {"HIGH": 60, "MEDIUM": 45, "LOW": 30}.get(impact.upper(), 30)
        score += EarningsWhispersCalendar.score_event(company, ticker, sector) - 45
        score += EarningsWhispersCalendar._market_cap_points(market_cap)
        return clamp_score(score)

    @staticmethod
    def _market_cap_points(market_cap: str) -> int:
        match = re.search(r"\$?([0-9.]+)\s*([BTM])", market_cap.replace(",", ""), flags=re.IGNORECASE)
        if not match:
            return 0
        value = float(match.group(1))
        unit = match.group(2).upper()
        billions = value * 1000 if unit == "T" else value if unit == "B" else value / 1000
        if billions >= 100:
            return 30
        if billions >= 25:
            return 22
        if billions >= 10:
            return 16
        if billions >= 2:
            return 8
        return 2

    @staticmethod
    def _select_key_earnings(events: list[EarningsEvent], limit: int) -> list[EarningsEvent]:
        """Select largest available earnings."""
        return sorted(
            events,
            key=lambda event: EarningsWhispersCalendar._market_cap_from_watch(event.watch),
            reverse=True,
        )[:limit]

    @staticmethod
    def _market_cap_from_watch(watch: str) -> float:
        match = re.search(r"Market cap:\s*\$?([0-9.]+)\s*([BTM])", watch, flags=re.IGNORECASE)
        if not match:
            return 0.0
        value = float(match.group(1))
        unit = match.group(2).upper()
        return value * 1000 if unit == "T" else value if unit == "B" else value / 1000


class FedWatchSource:
    """Runtime FOMC probability source using the no-key cme-fedwatch package."""

    def get_pricing(self) -> FomcMarketPricing:
        try:
            from cme_fedwatch import get_history, get_probabilities

            data = get_probabilities("next")
            meeting = (data.get("meetings") or [None])[0]
            if not meeting:
                raise ValueError("cme-fedwatch returned no upcoming meetings")

            probabilities = meeting.get("probabilities") or {}
            current_target = data.get("current_target", "")
            hold_probability = float(probabilities.get(current_target, 0.0))
            cut_probability = self._cut_probability(probabilities, current_target)
            direction = self._direction_vs_history(
                get_history("next", days=10),
                current_target,
                probabilities,
            )

            return FomcMarketPricing(
                next_fomc_date=date.fromisoformat(meeting["date"]),
                hold_probability=round(hold_probability, 1),
                cut_probability=round(cut_probability, 1),
                direction_vs_last_week=direction,
            )
        except Exception as exc:
            print(f"Warning: CME FedWatch probabilities unavailable ({exc}); continuing.")
            return FomcMarketPricing(
                next_fomc_date=None,
                hold_probability=0.0,
                cut_probability=0.0,
                direction_vs_last_week="Unavailable",
            )

    @staticmethod
    def _cut_probability(probabilities: dict[str, float], current_target: str) -> float:
        return FedWatchSource._rate_buckets(probabilities, current_target)["cut"]

    @staticmethod
    def _range_midpoint(target_range: str) -> float | None:
        match = re.fullmatch(r"\s*([0-9.]+)%?\s*-\s*([0-9.]+)%?\s*", target_range)
        if not match:
            return None
        low, high = (float(match.group(1)), float(match.group(2)))
        return (low + high) / 2

    @staticmethod
    def _rate_buckets(probabilities: dict[str, float], current_target: str) -> dict[str, float]:
        current_midpoint = FedWatchSource._range_midpoint(current_target)
        buckets = {"cut": 0.0, "hold": 0.0, "hike": 0.0}
        if current_midpoint is None:
            return buckets

        for target_range, probability in probabilities.items():
            midpoint = FedWatchSource._range_midpoint(target_range)
            if midpoint is None:
                continue
            if midpoint < current_midpoint:
                buckets["cut"] += float(probability)
            elif midpoint > current_midpoint:
                buckets["hike"] += float(probability)
            else:
                buckets["hold"] += float(probability)
        return buckets

    @staticmethod
    def _expected_rate(probabilities: dict[str, float]) -> float:
        total_probability = sum(float(value) for value in probabilities.values())
        if total_probability <= 0:
            return 0.0

        weighted_sum = 0.0
        for target_range, probability in probabilities.items():
            midpoint = FedWatchSource._range_midpoint(target_range)
            if midpoint is not None:
                weighted_sum += midpoint * float(probability)
        return weighted_sum / total_probability

    @staticmethod
    def _direction_vs_history(
            history_data: dict,
            current_target: str,
            current_probabilities: dict[str, float],
    ) -> str:
        prior = FedWatchSource._prior_probabilities(history_data)
        if not prior:
            current = FedWatchSource._rate_buckets(current_probabilities, current_target)
            return (
                "neutral vs last week unavailable "
                f"(hold {current['hold']:.1f}%, cut {current['cut']:.1f}%, "
                f"hike {current['hike']:.1f}%)"
            )

        prior_probabilities = prior["probabilities"]
        current = FedWatchSource._rate_buckets(current_probabilities, current_target)
        previous = FedWatchSource._rate_buckets(prior_probabilities, current_target)
        expected_delta = (
            FedWatchSource._expected_rate(current_probabilities)
            - FedWatchSource._expected_rate(prior_probabilities)
        )

        if expected_delta <= -0.005:
            direction = "dovish"
        elif expected_delta >= 0.005:
            direction = "hawkish"
        else:
            direction = "neutral"

        return (
            f"{direction} vs {prior['label']} "
            f"(hold {current['hold'] - previous['hold']:+.1f}pp, "
            f"cut {current['cut'] - previous['cut']:+.1f}pp, "
            f"hike {current['hike'] - previous['hike']:+.1f}pp)"
        )

    @staticmethod
    def _prior_probabilities(history_data: dict) -> dict | None:
        lookback = history_data.get("lookback") or []
        one_week = next((row for row in lookback if row.get("label") == "1w"), None)
        if one_week:
            return one_week

        history = history_data.get("history") or []
        if len(history) >= 2:
            prior = history[0]
            return {
                "label": prior.get("trade_date", "oldest available"),
                "probabilities": prior.get("probabilities", {}),
            }
        return None