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


@dataclass
class CommodityData:
    """Commodity price and weekly change data."""
    price: float
    weekly_change: float  # percentage change


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
    agent_type: str = "macro"


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
