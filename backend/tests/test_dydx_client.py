import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1 import perp_dex
from app.services.providers.dydx_client import DydxClient


def test_dydx_market_snapshot_normalizes_perpetual_markets() -> None:
    payload = {
        "markets": {
            "BTC-USD": {
                "ticker": "BTC-USD",
                "status": "ACTIVE",
                "oraclePrice": "65000",
                "priceChange24H": "1000",
                "volume24H": "12345678.9",
                "trades24H": 1234,
                "nextFundingRate": "0.000004",
                "initialMarginFraction": "0.02",
                "maintenanceMarginFraction": "0.012",
                "openInterest": "250",
                "tickSize": "1",
                "stepSize": "0.0001",
                "marketType": "CROSS",
            },
            "ETH-USD": {
                "ticker": "ETH-USD",
                "status": "ACTIVE",
                "oraclePrice": "3500",
                "openInterest": "1000",
            },
        }
    }

    snapshot = DydxClient.normalize_market_snapshot(payload, symbols=("BTC",))

    assert snapshot["status"] == "live"
    assert snapshot["read_only"] is True
    assert snapshot["execution_enabled"] is False
    assert len(snapshot["markets"]) == 1

    market = snapshot["markets"][0]
    assert market["symbol"] == "BTC"
    assert market["market"] == "BTC-USD"
    assert market["venue_id"] == "dydx"
    assert market["mark_price"] == pytest.approx(65000)
    assert market["oracle_price"] == pytest.approx(65000)
    assert market["prev_day_price"] == pytest.approx(64000)
    assert market["funding_rate"] == pytest.approx(0.000004)
    assert market["funding_pct"] == pytest.approx(0.0004)
    assert market["open_interest_base"] == pytest.approx(250)
    assert market["open_interest_usd"] == pytest.approx(16_250_000)
    assert market["volume_24h_usd"] == pytest.approx(12345678.9)
    assert market["trades_24h"] == 1234
    assert market["max_leverage"] == 50
    assert market["initial_margin_fraction"] == pytest.approx(0.02)
    assert market["maintenance_margin_fraction"] == pytest.approx(0.012)
    assert market["tick_size"] == pytest.approx(1)
    assert market["step_size"] == pytest.approx(0.0001)


def test_dydx_market_endpoint_uses_read_only_stub_client() -> None:
    class StubDydxClient:
        async def fetch_market_snapshot(self, symbols: tuple[str, ...]) -> dict:
            return {
                "venue_id": "dydx",
                "status": "live",
                "requested_symbols": list(symbols),
                "markets": [{"symbol": symbols[0], "mark_price": 100.0}],
                "read_only": True,
                "execution_enabled": False,
            }

    async def stub_client():
        yield StubDydxClient()

    app = FastAPI()
    app.include_router(perp_dex.router, prefix="/api/v1")
    app.dependency_overrides[perp_dex.get_dydx_client] = stub_client

    client = TestClient(app)
    response = client.get("/api/v1/perp-dex/venues/dydx/markets?symbols=btc,ETH,btc")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["meta"]["read_only"] is True
    assert payload["meta"]["external_provider_calls"] is True
    assert payload["meta"]["requested_symbols"] == ["BTC", "ETH"]
    assert payload["data"]["requested_symbols"] == ["BTC", "ETH"]
    assert payload["data"]["execution_enabled"] is False
