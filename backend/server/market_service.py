"""Market chart data for the frontend price charts (yfinance OHLC + EMA)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Final, cast

import pandas as pd
import yfinance as yf

DEFAULT_HISTORY_DAYS: Final[int] = 130
EMA_FAST_SPAN: Final[int] = 8
EMA_SLOW_SPAN: Final[int] = 21


@dataclass(frozen=True)
class Instrument:
    symbol: str
    name: str
    yahoo: str
    decimals: int


INSTRUMENTS: Final[dict[str, Instrument]] = {
    "SPX": Instrument("SPX", "S&P 500", "^GSPC", 0),
    "NDX": Instrument("NDX", "Nasdaq 100", "^NDX", 0),
    "IWM": Instrument("IWM", "Russell 2000", "IWM", 2),
    "GOLD": Instrument("GOLD", "Gold (Spot)", "GC=F", 1),
    "WTI": Instrument("WTI", "Crude Oil (WTI)", "CL=F", 2),
    "DXY": Instrument("DXY", "US Dollar Index", "DX-Y.NYB", 2),
}


def list_instruments() -> list[dict[str, str]]:
    instruments: list[dict[str, str]] = []
    for instrument in INSTRUMENTS.values():
        instruments.append(
            {
                "symbol": instrument.symbol,
                "name": instrument.name,
                "yahoo": instrument.yahoo,
            }
        )
    return instruments


def _round_to(value: float, decimals: int) -> float:
    factor = 10**decimals
    return round(value * factor) / factor


def _fetch_ohlcv(ticker: str, end_date: date, calendar_days: int) -> pd.DataFrame:
    """Download and clean daily OHLCV rows from Yahoo Finance."""
    start_date = end_date - timedelta(days=calendar_days)
    raw = yf.download(
        ticker,
        start=start_date.isoformat(),
        end=(end_date + timedelta(days=1)).isoformat(),
        progress=False,
        auto_adjust=True,
    )
    if raw is None or raw.empty:
        raise ValueError(f"No market data returned for {ticker}")

    df = cast(pd.DataFrame, raw)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    required = ["Open", "High", "Low", "Close"]
    missing: list[str] = []
    for column in required:
        if column not in df.columns:
            missing.append(column)
    if missing:
        raise ValueError(
            f"Market data for {ticker} missing columns: {', '.join(missing)}"
        )

    index = pd.DatetimeIndex(pd.to_datetime(df.index)).tz_localize(None)
    selected_columns = required.copy()
    if "Volume" in df.columns:
        selected_columns.append("Volume")

    cleaned_columns: dict[str, pd.Series] = {}
    for column in selected_columns:
        values = df[column].to_numpy()
        cleaned_columns[column] = pd.Series(values, index=index)
    df = pd.DataFrame(cleaned_columns)

    df = df.dropna(subset=["Open", "High", "Low", "Close"]).sort_index()
    df = df.loc[df.index <= pd.Timestamp(end_date)]
    df = df[df.index.weekday <= 4]

    if df.empty:
        raise ValueError(f"No trading data on or before {end_date} for {ticker}")
    return df.tail(DEFAULT_HISTORY_DAYS)


def _float_values(df: pd.DataFrame, column: str) -> list[float]:
    """Convert one pandas column to ordinary Python floats."""
    values: list[float] = []
    for value in df[column].to_numpy():
        values.append(float(value))
    return values


def _build_chart_series(
    df: pd.DataFrame,
    instrument: Instrument,
    ema8_series: pd.Series,
    ema21_series: pd.Series,
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """Convert pandas rows into the arrays expected by the chart library."""
    candles: list[dict] = []
    ema8: list[dict] = []
    ema21: list[dict] = []
    volume: list[dict] = []

    days: list[str] = []
    for timestamp in pd.DatetimeIndex(df.index):
        days.append(timestamp.date().isoformat())

    opens = _float_values(df, "Open")
    highs = _float_values(df, "High")
    lows = _float_values(df, "Low")
    closes = _float_values(df, "Close")

    has_volume = "Volume" in df.columns
    volumes: list[float] = []
    if has_volume:
        volumes = _float_values(df, "Volume")

    for index, day in enumerate(days):
        open_price = opens[index]
        close_price = closes[index]
        candles.append(
            {
                "time": day,
                "open": _round_to(open_price, instrument.decimals),
                "high": _round_to(highs[index], instrument.decimals),
                "low": _round_to(lows[index], instrument.decimals),
                "close": _round_to(close_price, instrument.decimals),
            }
        )
        ema8.append(
            {
                "time": day,
                "value": _round_to(
                    float(ema8_series.iloc[index]),
                    instrument.decimals,
                ),
            }
        )
        ema21.append(
            {
                "time": day,
                "value": _round_to(
                    float(ema21_series.iloc[index]),
                    instrument.decimals,
                ),
            }
        )

        if has_volume and volumes[index] > 0:
            is_up_day = close_price >= open_price
            color = "rgba(22,163,74,0.35)"
            if not is_up_day:
                color = "rgba(220,38,38,0.35)"
            volume.append(
                {
                    "time": day,
                    "value": int(volumes[index]),
                    "color": color,
                }
            )

    return candles, ema8, ema21, volume


def _market_stats(
    candles: list[dict],
    ema8: list[dict],
    ema21: list[dict],
    decimals: int,
) -> dict:
    """Calculate the summary values displayed above and below the chart."""
    last_close = candles[-1]["close"]
    previous_close = last_close
    if len(candles) > 1:
        previous_close = candles[-2]["close"]

    change = _round_to(last_close - previous_close, decimals)
    change_percent = 0.0
    if previous_close:
        change_percent = _round_to(
            (last_close - previous_close) / previous_close * 100,
            2,
        )

    highs: list[float] = []
    lows: list[float] = []
    for candle in candles:
        highs.append(candle["high"])
        lows.append(candle["low"])

    last_ema8 = ema8[-1]["value"]
    last_ema21 = ema21[-1]["value"]
    return {
        "last": last_close,
        "change": change,
        "changePct": change_percent,
        "periodHigh": _round_to(max(highs), decimals),
        "periodLow": _round_to(min(lows), decimals),
        "ema8": last_ema8,
        "ema21": last_ema21,
        "aboveEmas": last_close > last_ema8 and last_close > last_ema21,
    }


def build_market_history(
    symbol: str,
    *,
    end_date: date | None = None,
    history_days: int = DEFAULT_HISTORY_DAYS,
) -> dict:
    """Build one complete market-history response for the frontend."""
    key = symbol.upper()
    if key not in INSTRUMENTS:
        known = ", ".join(sorted(INSTRUMENTS))
        raise ValueError(f"Unknown symbol {symbol!r}. Known symbols: {known}")

    inst = INSTRUMENTS[key]
    as_of = end_date or date.today()
    # Request extra calendar days to allow for weekends and market holidays.
    calendar_days = max(history_days * 2, 260)
    df = _fetch_ohlcv(inst.yahoo, as_of, calendar_days)
    if len(df) > history_days:
        df = df.tail(history_days)

    closes = cast(pd.Series, df["Close"])
    ema8_series = cast(
        pd.Series,
        closes.ewm(span=EMA_FAST_SPAN, adjust=False).mean(),
    )
    ema21_series = cast(
        pd.Series,
        closes.ewm(span=EMA_SLOW_SPAN, adjust=False).mean(),
    )

    candles, ema8, ema21, volume = _build_chart_series(
        df,
        inst,
        ema8_series,
        ema21_series,
    )

    return {
        "symbol": inst.symbol,
        "name": inst.name,
        "yahoo": inst.yahoo,
        "decimals": inst.decimals,
        "candles": candles,
        "ema8": ema8,
        "ema21": ema21,
        "volume": volume,
        "stats": _market_stats(candles, ema8, ema21, inst.decimals),
    }
