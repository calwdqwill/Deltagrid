import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1 import perp_dex
from app.services.providers.aster_client import AsterClient


def test_aster_market_snapshot_normalizes_public_futures_market_data() -> None:
    exchange_info_payload = {
        "symbols": [
            {
                "symbol": "BTCUSDT",
                "contractType": "PERPETUAL",
                "status": "TRADING",
                "baseAsset": "BTC",
                "quoteAsset": "USDT",
                "liquidationFee": "0.025000",
                "marketTakeBound": "0.02",
                "filters": [
                    {"filterType": "PRICE_FILTER", "tickSize": "0.1"},
                    {"filterType": "LOT_SIZE", "stepSize": "0.001", "minQty": "0.001"},
                    {"filterType": "MIN_NOTIONAL", "notional": "5"},
                ],
            },
            {
                "symbol": "ETHUSDT",
                "contractType": "PERPETUAL",
                "status": "TRADING",
                "baseAsset": "ETH",
                "quoteAsset": "USDT",
                "filters": [],
            },
        ]
    }

    snapshot = AsterClient.normalize_market_snapshot(
        exchange_info_payload=exchange_info_payload,
        premium_payload=[
            {
                "symbol": "BTCUSDT",
                "markPrice": "65000",
                "indexPrice": "64950",
                "lastFundingRate": "0.0001",
                "interestRate": "0.0001",
                "nextFundingTime": 1781683200000,
            }
        ],
        ticker_payload=[
            {
                "symbol": "BTCUSDT",
                "openPrice": "64000",
                "priceChange": "1000",
                "priceChangePercent": "1.5625",
                "volume": "100.5",
                "quoteVolume": "6500000.5",
                "count": 1234,
            }
        ],
        book_ticker_payload=[
            {
                "symbol": "BTCUSDT",
                "bidPrice": "64999",
                "bidQty": "2.5",
                "askPrice": "65001",
                "askQty": "3.5",
            }
        ],
        open_interest_by_market={"BTCUSDT": {"symbol": "BTCUSDT", "openInterest": "123.45"}},
        symbols=("BTC",),
        depth_by_market={
            "BTCUSDT": {
                "lastUpdateId": 1,
                "bids": [["64999", "0.15"], ["64998", "0.30"]],
                "asks": [["65001", "0.10"], ["65002", "0.20"]],
            }
        },
    )

    assert snapshot["status"] == "live"
    assert snapshot["read_only"] is True
    assert snapshot["execution_enabled"] is False
    assert len(snapshot["markets"]) == 1

    market = snapshot["markets"][0]
    assert market["symbol"] == "BTC"
    assert market["market"] == "BTCUSDT"
    assert market["venue_id"] == "aster"
    assert market["normalization_status"] == "aster_public_futures_market_data"
    assert market["mark_price"] == pytest.approx(65000)
    assert market["mid_price"] == pytest.approx(65000)
    assert market["oracle_price"] == pytest.approx(64950)
    assert market["prev_day_price"] == pytest.approx(64000)
    assert market["funding_rate"] == pytest.approx(0.0001)
    assert market["funding_pct"] == pytest.approx(0.01)
    assert market["open_interest_base"] == pytest.approx(123.45)
    assert market["open_interest_usd"] == pytest.approx(8_024_250)
    assert market["volume_24h_usd"] == pytest.approx(6_500_000.5)
    assert market["volume_24h_base"] == pytest.approx(100.5)
    assert market["trades_24h"] == 1234
    assert market["bid_price"] == pytest.approx(64_999)
    assert market["ask_price"] == pytest.approx(65_001)
    assert market["top_of_book_spread_bps"] == pytest.approx(0.3076923077)
    assert market["top_of_book_spread_status"] == "display_only"
    assert market["orderbook_depth_status"] == "partial_ready_depth_ladder_display_only"
    assert market["orderbook_order_limit"] == 20
    assert market["orderbook_bid_orders"] == 2
    assert market["orderbook_ask_orders"] == 2
    assert market["best_bid_price"] == pytest.approx(64_999)
    assert market["best_ask_price"] == pytest.approx(65_001)
    assert market["best_bid_size_base"] == pytest.approx(0.15)
    assert market["best_ask_size_base"] == pytest.approx(0.10)
    assert market["bid_depth_top_orders_base"] == pytest.approx(0.45)
    assert market["ask_depth_top_orders_base"] == pytest.approx(0.30)
    assert market["bid_depth_top_orders_usd"] == pytest.approx((64999 * 0.15) + (64998 * 0.30))
    assert market["ask_depth_top_orders_usd"] == pytest.approx((65001 * 0.10) + (65002 * 0.20))
    assert "display Aster /fapi/v3/depth top levels only" in market["orderbook_depth_safe_use"]
    assert market["liquidation_fee"] == pytest.approx(0.025)
    assert market["market_take_bound"] == pytest.approx(0.02)
    assert market["tick_size"] == pytest.approx(0.1)
    assert market["step_size"] == pytest.approx(0.001)
    assert market["min_base_amount"] == pytest.approx(0.001)
    assert market["min_quote_amount"] == pytest.approx(5)
    assert "/fapi/v3/depth" in market["source_endpoint"]
    assert market["resolution_reason"] == "public futures market data and top depth levels are read-only diagnostics, not execution-grade routing input"


def test_aster_market_endpoint_uses_read_only_stub_client() -> None:
    class StubAsterClient:
        async def fetch_market_snapshot(self, symbols: tuple[str, ...]) -> dict:
            return {
                "venue_id": "aster",
                "status": "live",
                "requested_symbols": list(symbols),
                "markets": [{"symbol": symbols[0], "mark_price": 100.0}],
                "read_only": True,
                "execution_enabled": False,
            }

    async def stub_client():
        yield StubAsterClient()

    app = FastAPI()
    app.include_router(perp_dex.router, prefix="/api/v1")
    app.dependency_overrides[perp_dex.get_aster_client] = stub_client

    client = TestClient(app)
    response = client.get("/api/v1/perp-dex/venues/aster/markets?symbols=btc,ETH,btc")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["meta"]["read_only"] is True
    assert payload["meta"]["external_provider_calls"] is True
    assert payload["meta"]["source"] == "aster"
    assert payload["meta"]["requested_symbols"] == ["BTC", "ETH"]
    assert payload["meta"]["normalization_status"] == "aster_public_futures_market_data"
    assert payload["data"]["requested_symbols"] == ["BTC", "ETH"]
    assert payload["data"]["execution_enabled"] is False
