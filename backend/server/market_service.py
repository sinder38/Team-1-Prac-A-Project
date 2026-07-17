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
    return [
        {"symbol": inst.symbol, "name": inst.name, "yahoo": inst.yahoo}
        for inst in INSTRUMENTS.values()
    ]


def _round_to(value: float, decimals: int) -> float:
    factor = 10**decimals
    return round(value * factor) / factor


def _fetch_ohlcv(ticker: str, end_date: date, calendar_days: int) -> pd.DataFrame:
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
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Market data for {ticker} missing columns: {', '.join(missing)}")

    index = pd.DatetimeIndex(pd.to_datetime(df.index)).tz_localize(None)
    df = pd.DataFrame(
        {col: pd.Series(df[col].to_numpy(), index=index) for col in required + (["Volume"] if "Volume" in df.columns else [])},
    )
    df = df.dropna(subset=["Open", "High", "Low", "Close"]).sort_index()
    df = df.loc[df.index <= pd.Timestamp(end_date)]
    df = df[df.index.weekday <= 4]

    if df.empty:
        raise ValueError(f"No trading data on or before {end_date} for {ticker}")
    return df.tail(DEFAULT_HISTORY_DAYS)


def build_market_history(
    symbol: str,
    *,
    end_date: date | None = None,
    history_days: int = DEFAULT_HISTORY_DAYS,
) -> dict:
    key = symbol.upper()
    if key not in INSTRUMENTS:
        known = ", ".join(sorted(INSTRUMENTS))
        raise ValueError(f"Unknown symbol {symbol!r}. Known symbols: {known}")

    inst = INSTRUMENTS[key]
    as_of = end_date or date.today()
    # Extra calendar days so ~130 trading sessions are available after weekends/holidays.
    calendar_days = max(history_days * 2, 260)
    df = _fetch_ohlcv(inst.yahoo, as_of, calendar_days)
    if len(df) > history_days:
        df = df.tail(history_days)

    closes = cast(pd.Series, df["Close"])
    ema8_series = closes.ewm(span=EMA_FAST_SPAN, adjust=False).mean()
    ema21_series = closes.ewm(span=EMA_SLOW_SPAN, adjust=False).mean()

    candles: list[dict] = []
    ema8: list[dict] = []
    ema21: list[dict] = []
    volume: list[dict] = []
    has_volume = "Volume" in df.columns

    for idx, (ts, row) in enumerate(df.iterrows()):
        day = ts.date().isoformat()
        open_ = float(row["Open"])
        high = float(row["High"])
        low = float(row["Low"])
        close = float(row["Close"])
        up = close >= open_

        candles.append(
            {
                "time": day,
                "open": _round_to(open_, inst.decimals),
                "high": _round_to(high, inst.decimals),
                "low": _round_to(low, inst.decimals),
                "close": _round_to(close, inst.decimals),
            }
        )
        ema8.append({"time": day, "value": _round_to(float(ema8_series.iloc[idx]), inst.decimals)})
        ema21.append({"time": day, "value": _round_to(float(ema21_series.iloc[idx]), inst.decimals)})

        if has_volume:
            vol = float(row["Volume"])
            if vol > 0:
                volume.append(
                    {
                        "time": day,
                        "value": int(vol),
                        "color": "rgba(22,163,74,0.35)" if up else "rgba(220,38,38,0.35)",
                    }
                )

    last = candles[-1]["close"]
    prev = candles[-2]["close"] if len(candles) > 1 else last
    change = _round_to(last - prev, inst.decimals)
    change_pct = _round_to(((last - prev) / prev) * 100, 2) if prev else 0.0
    period_high = max(c["high"] for c in candles)
    period_low = min(c["low"] for c in candles)
    last_ema8 = ema8[-1]["value"]
    last_ema21 = ema21[-1]["value"]

    return {
        "symbol": inst.symbol,
        "name": inst.name,
        "yahoo": inst.yahoo,
        "decimals": inst.decimals,
        "candles": candles,
        "ema8": ema8,
        "ema21": ema21,
        "volume": volume,
        "stats": {
            "last": last,
            "change": change,
            "changePct": change_pct,
            "periodHigh": _round_to(period_high, inst.decimals),
            "periodLow": _round_to(period_low, inst.decimals),
            "ema8": last_ema8,
            "ema21": last_ema21,
            "aboveEmas": last > last_ema8 and last > last_ema21,
        },
    }
