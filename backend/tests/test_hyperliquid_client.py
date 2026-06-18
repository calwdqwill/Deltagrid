import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1 import perp_dex
from app.services.providers.hyperliquid_client import HyperliquidClient


def test_hyperliquid_market_snapshot_normalizes_context_rows() -> None:
    payload = [
        {
            "universe": [
                {"name": "BTC", "szDecimals": 5, "maxLeverage": 50},
                {"name": "ETH", "szDecimals": 4, "maxLeverage": 25},
            ]
        },
        [
            {
                "markPx": "65000.5",
                "midPx": "65001.0",
                "oraclePx": "64990.0",
                "prevDayPx": "64000.0",
                "funding": "0.0000125",
                "openInterest": "25000",
                "dayNtlVlm": "123456789.5",
                "dayBaseVlm": "1900.25",
                "premium": "0.00042",
                "impactPxs": ["64999.0", "65002.0"],
            },
            {"markPx": "3500", "funding": "-0.00001", "openInterest": "100000"},
        ],
    ]

    snapshot = HyperliquidClient.normalize_market_snapshot(payload, symbols=("BTC",))

    assert snapshot["status"] == "live"
    assert snapshot["read_only"] is True
    assert snapshot["execution_enabled"] is False
    assert len(snapshot["markets"]) == 1

    market = snapshot["markets"][0]
    assert market["symbol"] == "BTC"
    assert market["market"] == "BTC-PERP"
    assert market["venue_id"] == "hyperliquid"
    assert market["mark_price"] == pytest.approx(65000.5)
    assert market["funding_rate"] == pytest.approx(0.0000125)
    assert market["funding_pct"] == pytest.approx(0.00125)
    assert market["open_interest_base"] == pytest.approx(25000)
    assert market["open_interest_usd"] == pytest.approx(1_625_012_500)
    assert market["volume_24h_usd"] == pytest.approx(123456789.5)
    assert market["premium_pct"] == pytest.approx(0.042)
    assert market["impact_bid_price"] == pytest.approx(64999.0)
    assert market["impact_ask_price"] == pytest.approx(65002.0)
    assert market["max_leverage"] == 50
    assert market["sz_decimals"] == 5


def test_hyperliquid_market_endpoint_uses_read_only_stub_client() -> None:
    class StubHyperliquidClient:
        async def fetch_market_snapshot(self, symbols: tuple[str, ...], dex: str = "") -> dict:
            return {
                "venue_id": "hyperliquid",
                "status": "live",
                "requested_symbols": list(symbols),
                "dex": dex or None,
                "markets": [{"symbol": symbols[0], "mark_price": 100.0}],
                "read_only": True,
                "execution_enabled": False,
            }

    async def stub_client():
        yield StubHyperliquidClient()

    app = FastAPI()
    app.include_router(perp_dex.router, prefix="/api/v1")
    app.dependency_overrides[perp_dex.get_hyperliquid_client] = stub_client

    client = TestClient(app)
    response = client.get("/api/v1/perp-dex/venues/hyperliquid/markets?symbols=btc,ETH,btc&dex=test-dex")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["meta"]["read_only"] is True
    assert payload["meta"]["external_provider_calls"] is True
    assert payload["meta"]["requested_symbols"] == ["BTC", "ETH"]
    assert payload["data"]["requested_symbols"] == ["BTC", "ETH"]
    assert payload["data"]["dex"] == "test-dex"
    assert payload["data"]["execution_enabled"] is False
