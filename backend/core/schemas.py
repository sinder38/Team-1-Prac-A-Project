from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class Bias(str, Enum):
    BULLISH = "Bullish"
    BEARISH = "Bearish"
    NEUTRAL = "Neutral"
    MIXED = "Mixed"
    UNCERTAIN = "Uncertain"


class Confidence(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    LOW_MEDIUM = "Low-Medium"


class MacroBias(str, Enum):
    HAWKISH = "Hawkish"
    DOVISH = "Dovish"
    NEUTRAL = "Neutral"
    BINARY_RISK = "Binary-risk"


class Regime(str, Enum):
    BULLISH = "Bullish"
    BEARISH = "Bearish"
    NEUTRAL = "Neutral"
    UNCERTAIN = "Uncertain"
    MIXED = "Mixed"


@dataclass
class InstrumentTechnical:
    last_close: float
    ema_8: float
    ema_21: float
    trend_bias: Bias
    key_support: float
    key_resistance: float
    confidence: Confidence


@dataclass
class TechnicalOutput:
    prediction_date: date
    instruments: dict[str, InstrumentTechnical]  # expected keys: "SPX", "NDX", "IWM"
    agent_type: str = "technical"
    horizon_days: int = 7


@dataclass
class SectorSignal:
    sector: str  # e.g. "Technology", "Banking"
    bias: Bias
    window: str  # e.g. "seasonal LONG (March–July)"


@dataclass
class AlmanacOutput:
    prediction_date: date
    monthly_bias: Bias
    seasonal_bias: Bias
    confidence: Confidence
    thesis: str
    weekly_pattern: str = ""
    sector_signals: list[SectorSignal] = field(default_factory=list)
    agent_type: str = "almanac"
    horizon_days: int = 7


@dataclass
class CommodityData:
    """Commodity price and weekly change data."""
    price: float
    weekly_change: float  # percentage change
    direction: str = ""


@dataclass
class CalendarEvent:
    """Week-ahead macro calendar event."""
    date_label: str
    name: str
    impact: str
    expected: str = "N/A"
    previous: str = "N/A"
    priority: int = 0
    source_url: str = ""


@dataclass
class MacroOutput:
    prediction_date: date
    fed_rate: str
    yield_2y: float
    yield_10y: float
    yield_30y: float
    dxy: CommodityData
    wti_oil: CommodityData
    gold: CommodityData
    macro_bias: MacroBias
    primary_driver: str
    confidence: Confidence
    invalidation: str
    next_fomc_date: date | None = None
    hold_probability: float = 0.0
    cut_probability: float = 0.0
    fomc_direction: str = "N/A"
    yield_curve: str = "N/A"
    yield_10y_direction: str = "N/A"
    week_ahead_calendar: list[CalendarEvent] = field(default_factory=list)
    key_earnings: list[str] = field(default_factory=list)
    confirmed_news: list[str] = field(default_factory=list)
    agent_type: str = "macro"
    horizon_days: int = 7


@dataclass
class PredictedRange:
    low: float
    high: float


@dataclass
class LLMOutput:
    prediction_date: date
    model_name: str
    weekly_regime: Regime
    confidence: Confidence
    spx_range: PredictedRange
    ndx_range: PredictedRange
    iwm_range: PredictedRange
    invalidation: str
    plain_english: str
    supporting_evidence: list[str] = field(default_factory=list)  # max 3
    contradictions: list[str] = field(default_factory=list)  # max 2
    agent_type: str = "llm"


@dataclass
class EvidenceOutput:
    prediction_date: date
    week: str          # e.g. "W25"
    content: str       # raw markdown text
    agent_type: str = "evidence"
