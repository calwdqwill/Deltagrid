import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1 import perp_dex
from app.services.providers.lighter_client import LighterClient


def test_lighter_market_snapshot_normalizes_public_market_details() -> None:
    order_books_payload = {
        "code": 200,
        "order_books": [
            {
                "symbol": "BTC",
                "market_id": 1,
                "market_type": "perp",
                "status": "active",
                "maker_fee": "0.0000",
                "taker_fee": "0.0000",
                "liquidation_fee": "1.0000",
                "min_base_amount": "0.00020",
                "min_quote_amount": "10.000000",
                "supported_size_decimals": 5,
                "supported_price_decimals": 1,
            },
            {
                "symbol": "ETH",
                "market_id": 0,
                "market_type": "perp",
                "status": "active",
            },
        ],
    }
    details_by_market_id = {
        1: {
            "last_trade_price": 65000.5,
            "daily_trades_count": 12345,
            "daily_base_token_volume": 2500.25,
            "daily_quote_token_volume": 162501250.5,
            "daily_price_change": 0.0123,
            "open_interest": 200.5,
            "default_initial_margin_fraction": 500,
            "maintenance_margin_fraction": 120,
        }
    }
    orders_by_market_id = {
        1: {
            "code": 200,
            "total_asks": 2,
            "asks": [
                {"price": "65002", "remaining_base_amount": "0.20"},
                {"price": "65001", "remaining_base_amount": "0.10"},
            ],
            "total_bids": 2,
            "bids": [
                {"price": "64998", "remaining_base_amount": "0.30"},
                {"price": "64999", "remaining_base_amount": "0.15"},
            ],
        }
    }
    funding_by_market_id = {1: -0.000104}

    snapshot = LighterClient.normalize_market_snapshot(
        order_books_payload=order_books_payload,
        details_by_market_id=details_by_market_id,
        funding_by_market_id=funding_by_market_id,
        symbols=("BTC",),
        orders_by_market_id=orders_by_market_id,
    )

    assert snapshot["status"] == "live"
    assert snapshot["read_only"] is True
    assert snapshot["execution_enabled"] is False
    assert len(snapshot["markets"]) == 1

    market = snapshot["markets"][0]
    assert market["symbol"] == "BTC"
    assert market["market"] == "BTC-PERP"
    assert market["venue_id"] == "lighter"
    assert market["normalization_status"] == "lighter_public_market_details"
    assert market["mark_price"] == pytest.approx(65000.5)
    assert market["price_source"] == "last_trade_price"
    assert market["funding_rate"] == pytest.approx(-0.000104)
    assert market["funding_pct"] == pytest.approx(-0.0104)
    assert market["open_interest_base"] == pytest.approx(200.5)
    assert market["open_interest_usd"] == pytest.approx(13_032_600.25)
    assert market["volume_24h_usd"] == pytest.approx(162501250.5)
    assert market["volume_24h_base"] == pytest.approx(2500.25)
    assert market["trades_24h"] == 12345
    assert market["max_leverage"] == 20
    assert market["initial_margin_fraction"] == pytest.approx(0.05)
    assert market["maintenance_margin_fraction"] == pytest.approx(0.012)
    assert market["orderbook_depth_status"] == "partial_ready_top_orders_only"
    assert market["orderbook_order_limit"] == 25
    assert market["orderbook_bid_orders"] == 2
    assert market["orderbook_ask_orders"] == 2
    assert market["best_bid_price"] == pytest.approx(64999)
    assert market["best_ask_price"] == pytest.approx(65001)
    assert market["best_bid_size_base"] == pytest.approx(0.15)
    assert market["best_ask_size_base"] == pytest.approx(0.10)
    assert market["top_of_book_spread_bps"] == pytest.approx(0.3076923077)
    assert market["bid_depth_top_orders_base"] == pytest.approx(0.45)
    assert market["ask_depth_top_orders_base"] == pytest.approx(0.30)
    assert market["bid_depth_top_orders_usd"] == pytest.approx((64999 * 0.15) + (64998 * 0.30))
    assert market["ask_depth_top_orders_usd"] == pytest.approx((65001 * 0.10) + (65002 * 0.20))
    assert "display top resting orders only" in market["orderbook_depth_safe_use"]
    assert market["tick_size"] == pytest.approx(0.1)
    assert market["step_size"] == pytest.approx(0.00001)
    assert market["resolution_reason"] == "public market details and top order depth are read-only diagnostics, not execution-grade routing input"


def test_lighter_market_endpoint_uses_read_only_stub_client() -> None:
    class StubLighterClient:
        async def fetch_market_snapshot(self, symbols: tuple[str, ...]) -> dict:
            return {
                "venue_id": "lighter",
                "status": "live",
                "requested_symbols": list(symbols),
                "markets": [{"symbol": symbols[0], "mark_price": 100.0}],
                "read_only": True,
                "execution_enabled": False,
            }

    async def stub_client():
        yield StubLighterClient()

    app = FastAPI()
    app.include_router(perp_dex.router, prefix="/api/v1")
    app.dependency_overrides[perp_dex.get_lighter_client] = stub_client

    client = TestClient(app)
    response = client.get("/api/v1/perp-dex/venues/lighter/markets?symbols=btc,ETH,btc")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["meta"]["read_only"] is True
    assert payload["meta"]["external_provider_calls"] is True
    assert payload["meta"]["source"] == "lighter"
    assert payload["meta"]["requested_symbols"] == ["BTC", "ETH"]
    assert payload["meta"]["normalization_status"] == "lighter_public_market_details"
    assert payload["data"]["requested_symbols"] == ["BTC", "ETH"]
    assert payload["data"]["execution_enabled"] is False


def test_lighter_market_snapshot_keeps_zero_market_id() -> None:
    snapshot = LighterClient.normalize_market_snapshot(
        order_books_payload={
            "code": 200,
            "order_books": [
                {
                    "symbol": "ETH",
                    "market_id": 0,
                    "market_type": "perp",
                    "status": "active",
                    "maker_fee": "0.0000",
                    "taker_fee": "0.0000",
                }
            ],
        },
        details_by_market_id={
            0: {
                "last_trade_price": 3500.0,
                "open_interest": 10.0,
                "daily_quote_token_volume": 1000000.0,
            }
        },
        funding_by_market_id={0: 0.000095},
        symbols=("ETH",),
    )

    market = snapshot["markets"][0]
    assert market["status"] == "live"
    assert market["market_id"] == 0
    assert market["mark_price"] == pytest.approx(3500.0)
    assert market["funding_rate"] == pytest.approx(0.000095)
    assert market["open_interest_usd"] == pytest.approx(35000.0)
