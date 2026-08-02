from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from agents.evidence.evidence_agent import EvidenceAgent
from agents.evidence.models import (
    BITCOIN_SPEC,
    BONDS_SPEC,
    GOLD_SPEC,
    INDEX_SPECS,
    OIL_SPEC,
    PERFORMANCE_CHART_SPECS,
    SECTOR_SPECS,
    VIX_SPEC,
)
from core.schemas import EvidenceOutput


class _FakeMarketDataProvider:
    def __init__(self):
        self.calls: list[str] = []
        self.values = {
            "^GSPC": (100.0, 102.0),
            "^NDX": (100.0, 103.0),
            "^DJI": (100.0, 101.0),
            "IWM": (100.0, 99.0),
            "CL=F": (80.0, 78.0),
            "NG=F": (3.0, 3.1),
            "GC=F": (2000.0, 2010.0),
            "SI=F": (30.0, 29.0),
            "HG=F": (4.0, 4.1),
            "ZN=F": (110.0, 109.0),
            "TLT": (90.0, 91.0),
            "EURUSD=X": (1.10, 1.11),
            "^VIX": (20.0, 18.0),
            "BTC-USD": (60000.0, 63000.0),
            "XLK": (100.0, 105.0),
            "XLE": (100.0, 96.0),
            "XLF": (100.0, 101.0),
            "XLY": (100.0, 99.0),
            "XLP": (100.0, 102.0),
            "XLI": (100.0, 100.5),
            "XLB": (100.0, 104.0),
            "XLV": (100.0, 100.25),
            "XLU": (100.0, 97.0),
            "XLRE": (100.0, 98.0),
            "XLC": (100.0, 103.0),
        }

    def history(self, ticker: str, start: date, end: date) -> pd.Series:
        self.calls.append(ticker)
        previous, current = self.values[ticker]
        dates = pd.to_datetime(
            [
                "2026-06-12",
                "2026-06-15",
                "2026-06-16",
                "2026-06-17",
                "2026-06-18",
                "2026-06-19",
            ]
        )
        prices = [
            previous,
            current * 0.96,
            current * 0.97,
            current * 0.98,
            current * 0.99,
            current,
        ]
        return pd.Series(prices, index=dates)


class _FakeYieldDataProvider:
    def __init__(self):
        self.calls: list[str] = []

    def history(self, series_id: str, start: date, end: date) -> pd.Series:
        self.calls.append(series_id)
        dates = pd.to_datetime(
            [
                "2026-06-12",
                "2026-06-15",
                "2026-06-16",
                "2026-06-17",
                "2026-06-18",
                "2026-06-19",
            ]
        )
        return pd.Series([4.50, 4.48, 4.47, 4.46, 4.45, 4.44], index=dates)


class _MissingYieldDataProvider:
    def history(self, series_id: str, start: date, end: date) -> pd.Series:
        return pd.Series(dtype=float)


def test_run_returns_generated_evidence_output(tmp_path):
    provider = _FakeMarketDataProvider()

    agent = EvidenceAgent(
        data_root=tmp_path,
        market_data_provider=provider,
        yield_data_provider=_FakeYieldDataProvider(),
    )
    result = agent.run(date(2026, 6, 16))

    assert isinstance(result, EvidenceOutput)
    assert result.week == "W25"
    assert result.content.startswith("# Week 05 Market Report (2026)")
    assert "**Week ended:** Friday, June 19, 2026" in result.content
    assert "| S&P 500" in result.content
    assert "| SPX | 102.00 | **Up 2.00%** |" in result.content
    assert "[finviz_1W_2026_W25.png](./finviz_1W_2026_W25.png)" in result.content
    assert "[finviz_sectors_5D_2026_W25.png](./finviz_sectors_5D_2026_W25.png)" in result.content
    assert "| **10-Year interest rate** | 4.44% | **Slightly lower (about 0.06 points)** |" in result.content
    assert "## 11 Parts of the Stock Market" in result.content
    assert result.prediction_date == date(2026, 6, 16)
    assert result.agent_type == "evidence"


def test_run_does_not_require_manual_actuals_file(tmp_path):
    provider = _FakeMarketDataProvider()

    agent = EvidenceAgent(
        data_root=tmp_path,
        market_data_provider=provider,
        yield_data_provider=_FakeYieldDataProvider(),
    )
    result = agent.run(date(2026, 6, 16))

    assert result.week == "W25"
    assert "10-year Treasury yield from FRED series DGS10" in result.content


def test_run_fetches_expected_market_tickers(tmp_path):
    provider = _FakeMarketDataProvider()

    agent = EvidenceAgent(
        data_root=tmp_path,
        market_data_provider=provider,
        yield_data_provider=_FakeYieldDataProvider(),
    )
    result = agent.run(date(2026, 6, 16))

    expected_tickers = {
        *(spec.ticker for spec in INDEX_SPECS),
        GOLD_SPEC.ticker,
        OIL_SPEC.ticker,
        BONDS_SPEC.ticker,
        VIX_SPEC.ticker,
        BITCOIN_SPEC.ticker,
        *(spec.ticker for spec in SECTOR_SPECS),
        *(ticker for _, ticker in PERFORMANCE_CHART_SPECS),
    }
    assert result.week == "W25"
    assert expected_tickers.issubset(set(provider.calls))


def test_render_md_returns_generated_content(tmp_path):
    provider = _FakeMarketDataProvider()
    agent = EvidenceAgent(
        data_root=tmp_path,
        market_data_provider=provider,
        yield_data_provider=_FakeYieldDataProvider(),
    )
    result = agent.run(date(2026, 6, 16))

    assert agent.render_md(result, date(2026, 6, 16)) == result.content


def test_missing_yield_data_does_not_crash(tmp_path):
    agent = EvidenceAgent(
        data_root=tmp_path,
        market_data_provider=_FakeMarketDataProvider(),
        yield_data_provider=_MissingYieldDataProvider(),
    )

    result = agent.run(date(2026, 6, 16))

    assert "| **10-Year interest rate** | N/A | **N/A** |" in result.content


def test_render_includes_existing_technical_chart_links(tmp_path):
    charts_dir = tmp_path / "charts"
    charts_dir.mkdir()
    for symbol in ("SPX", "NDX", "IWM"):
        (charts_dir / f"technical_{symbol}_2026-W25.png").write_bytes(b"png")

    agent = EvidenceAgent(
        data_root=tmp_path,
        market_data_provider=_FakeMarketDataProvider(),
        yield_data_provider=_FakeYieldDataProvider(),
    )

    result = agent.run(date(2026, 6, 16))

    assert "S&P 500 daily chart (ProRealTime)" in result.content
    assert "[../charts/technical_SPX_2026-W25.png](../charts/technical_SPX_2026-W25.png)" in result.content
    assert "ProRealTime daily chart screenshots generated by the technical agent" in result.content