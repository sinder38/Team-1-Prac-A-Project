import json
from datetime import date
from unittest.mock import patch

import pandas as pd
import pytest
from server import create_app
from server.market_service import build_market_history


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _sample_ohlcv(rows: int = 30) -> pd.DataFrame:
    dates = pd.bdate_range(end="2026-06-05", periods=rows)
    closes = [100 + i * 0.5 for i in range(rows)]
    return pd.DataFrame(
        {
            "Open": [c - 0.2 for c in closes],
            "High": [c + 0.4 for c in closes],
            "Low": [c - 0.4 for c in closes],
            "Close": closes,
            "Volume": [1_000_000 + i * 1000 for i in range(rows)],
        },
        index=dates,
    )


def test_get_instruments(client):
    resp = client.get("/market/instruments")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    symbols = {item["symbol"] for item in data}
    assert symbols == {"SPX", "NDX", "IWM", "GOLD", "WTI", "DXY"}


def test_get_history_missing_symbol(client):
    resp = client.get("/market/history")
    assert resp.status_code == 400
    assert "symbol" in json.loads(resp.data)["error"]


def test_get_history_unknown_symbol(client):
    resp = client.get("/market/history?symbol=FAKE")
    assert resp.status_code == 400
    assert "Unknown symbol" in json.loads(resp.data)["error"]


def test_get_history_success(client):
    with patch("server.market_service.yf.download", return_value=_sample_ohlcv()):
        resp = client.get("/market/history?symbol=SPX&days=20")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["symbol"] == "SPX"
    assert len(data["candles"]) == 20
    assert len(data["ema8"]) == 20
    assert len(data["ema21"]) == 20
    assert data["stats"]["last"] == data["candles"][-1]["close"]
    assert "changePct" in data["stats"]
    assert isinstance(data["stats"]["aboveEmas"], bool)


def test_get_history_invalid_end_date(client):
    resp = client.get("/market/history?symbol=SPX&end_date=not-a-date")
    assert resp.status_code == 400


def test_build_market_history_empty_download():
    with patch("server.market_service.yf.download", return_value=pd.DataFrame()):
        with pytest.raises(ValueError, match="No market data"):
            build_market_history("SPX", end_date=date(2026, 6, 5), history_days=10)
