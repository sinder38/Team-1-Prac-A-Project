"""Market data sources used by the evidence report."""

from __future__ import annotations

from datetime import date, timedelta
from io import StringIO
from typing import Final, cast

import pandas as pd
import requests
import yfinance as yf


class YahooFinanceEvidenceProvider:
    """Fetch adjusted closes for indexes, ETFs, commodities, VIX, and crypto."""

    def history(self, ticker: str, start: date, end: date) -> pd.Series:
        raw = yf.download(
            ticker,
            start=start.isoformat(),
            end=(end + timedelta(days=1)).isoformat(),
            progress=False,
            auto_adjust=True,
        )
        if raw is None or raw.empty:
            raise ValueError(f"No market data was returned for {ticker}.")

        close = self._close_column(raw, ticker)
        close = pd.Series(
            close.to_numpy(),
            index=pd.DatetimeIndex(pd.to_datetime(close.index)).tz_localize(None),
            name=close.name,
        )
        close = cast(pd.Series, close.dropna().sort_index())
        if close.empty:
            raise ValueError(f"No closing prices were returned for {ticker}.")
        return close

    @staticmethod
    def _close_column(raw: pd.DataFrame, ticker: str) -> pd.Series:
        if isinstance(raw.columns, pd.MultiIndex):
            if "Close" in raw.columns.get_level_values(0):
                close = raw["Close"]
            elif "Close" in raw.columns.get_level_values(-1):
                close = raw.xs("Close", axis=1, level=-1)
            else:
                raise ValueError(f"Market data for {ticker} did not include closes.")

            if isinstance(close, pd.DataFrame):
                if ticker in close.columns:
                    return cast(pd.Series, close[ticker])
                return cast(pd.Series, close.iloc[:, 0])
            return cast(pd.Series, close)

        if "Close" not in raw.columns:
            raise ValueError(f"Market data for {ticker} did not include closes.")
        close = raw["Close"]
        if isinstance(close, pd.DataFrame):
            return cast(pd.Series, close.iloc[:, 0])
        return cast(pd.Series, close)


class FredYieldProvider:
    """Fetch Treasury yields from FRED's public CSV endpoint."""

    _url: Final[str] = "https://fred.stlouisfed.org/graph/fredgraph.csv"

    def history(self, series_id: str, start: date, end: date) -> pd.Series:
        response = requests.get(self._url, params={"id": series_id}, timeout=30)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text))
        if "observation_date" not in df.columns or series_id not in df.columns:
            raise ValueError(f"FRED did not return the {series_id} series.")

        raw_values = cast(pd.Series, df[series_id])
        values = cast(pd.Series, pd.to_numeric(raw_values, errors="coerce"))
        raw_dates = cast(pd.Series, df["observation_date"])
        dates = pd.DatetimeIndex(pd.to_datetime(raw_dates))
        series = pd.Series(values.to_numpy(), index=dates)
        series = cast(pd.Series, series.dropna().sort_index())
        index = pd.DatetimeIndex(series.index)
        filtered = [
            (item, float(value))
            for item, value in zip(index, series.to_numpy())
            if start <= item.date() <= end
        ]
        if not filtered:
            raise ValueError(f"FRED did not return {series_id} data for this week.")
        return pd.Series(
            [value for _, value in filtered],
            index=pd.DatetimeIndex([item for item, _ in filtered]),
        )