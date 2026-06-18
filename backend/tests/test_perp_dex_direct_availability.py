import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1 import perp_dex


def _app_with_override(dependency, stub_client) -> TestClient:
    async def override():
        yield stub_client

    app = FastAPI()
    app.include_router(perp_dex.router, prefix="/api/v1")
    app.dependency_overrides[dependency] = override
    return TestClient(app)


def test_direct_venue_endpoint_adds_availability_summary() -> None:
    class StubLighterClient:
        async def fetch_market_snapshot(self, symbols: tuple[str, ...]) -> dict:
            return {
                "venue_id": "lighter",
                "venue_name": "Lighter",
                "source": "lighter_order_books_details",
                "status": "live",
                "requested_symbols": list(symbols),
                "markets": [
                    {
                        "symbol": "BTC",
                        "market": "BTC-PERP",
                        "status": "live",
                        "provider_status": "active",
                        "orderbook_depth_status": "partial_ready_top_orders_only",
                    }
                ],
                "fetched_at": "2026-06-18T00:00:00+00:00",
                "read_only": True,
                "execution_enabled": False,
            }

    client = _app_with_override(perp_dex.get_lighter_client, StubLighterClient())
    response = client.get("/api/v1/perp-dex/venues/lighter/markets?symbols=btc,eth")

    assert response.status_code == 200
    payload = response.json()
    summary = payload["data"]["availability_summary"]
    assert summary == payload["meta"]["availability_summary"]
    assert summary["venue_id"] == "lighter"
    assert summary["status"] == "live"
    assert summary["provider_error_class"] is None
    assert summary["rows"] == 1
    assert summary["requested_symbols"] == ["BTC", "ETH"]
    assert summary["matched_symbols"] == ["BTC"]
    assert summary["missing_symbols"] == ["ETH"]
    assert summary["market_status_counts"] == {"live": 1}
    assert summary["provider_status_counts"] == {"active": 1}
    assert summary["depth_diagnostics"] == {
        "available": True,
        "market_count": 1,
        "statuses": ["partial_ready_top_orders_only"],
    }
    assert summary["read_only"] is True
    assert summary["execution_enabled"] is False
    assert summary["ranking_enabled"] is False
    assert summary["production_signal_enabled"] is False


def test_direct_venue_availability_summary_classifies_schema_drift_snapshot() -> None:
    class StubHyperliquidClient:
        async def fetch_market_snapshot(self, symbols: tuple[str, ...], dex: str = "") -> dict:
            return {
                "venue_id": "hyperliquid",
                "venue_name": "Hyperliquid",
                "source": "hyperliquid_info_metaAndAssetCtxs",
                "status": "empty",
                "dex": dex or None,
                "requested_symbols": list(symbols),
                "markets": [],
                "fetched_at": "2026-06-18T00:00:00+00:00",
                "read_only": True,
                "execution_enabled": False,
                "reason": "missing_universe",
            }

    client = _app_with_override(perp_dex.get_hyperliquid_client, StubHyperliquidClient())
    response = client.get("/api/v1/perp-dex/venues/hyperliquid/markets?symbols=btc")

    assert response.status_code == 200
    summary = response.json()["data"]["availability_summary"]
    assert summary["status"] == "empty"
    assert summary["provider_error_class"] == "schema_drift"
    assert summary["rows"] == 0
    assert summary["missing_symbols"] == ["BTC"]
    assert summary["read_only"] is True
    assert summary["execution_enabled"] is False


def test_direct_venue_error_detail_preserves_read_only_boundary() -> None:
    class TimeoutDydxClient:
        async def fetch_market_snapshot(self, symbols: tuple[str, ...]) -> dict:
            raise httpx.ReadTimeout("timed out")

    client = _app_with_override(perp_dex.get_dydx_client, TimeoutDydxClient())
    response = client.get("/api/v1/perp-dex/venues/dydx/markets?symbols=btc,eth")

    assert response.status_code == 502
    detail = response.json()["detail"]
    assert detail["provider_error_class"] == "timeout"
    assert detail["read_only"] is True
    assert detail["execution_enabled"] is False
    assert detail["ranking_enabled"] is False
    assert detail["production_signal_enabled"] is False
    summary = detail["availability_summary"]
    assert summary["status"] == "unavailable"
    assert summary["provider_error_class"] == "timeout"
    assert summary["requested_symbols"] == ["BTC", "ETH"]
    assert summary["read_only"] is True
    assert summary["execution_enabled"] is False


def test_direct_provider_error_classifier_covers_release_taxonomy() -> None:
    request = httpx.Request("GET", "https://provider.example.test/markets")
    rate_limit = httpx.Response(429, request=request)
    missing_endpoint = httpx.Response(404, request=request)
    unavailable = httpx.Response(503, request=request)

    assert perp_dex._provider_error_class_from_exception(httpx.ReadTimeout("timed out")) == "timeout"
    assert (
        perp_dex._provider_error_class_from_exception(
            httpx.HTTPStatusError("rate limited", request=request, response=rate_limit)
        )
        == "rate_limit"
    )
    assert (
        perp_dex._provider_error_class_from_exception(
            httpx.HTTPStatusError("missing", request=request, response=missing_endpoint)
        )
        == "unavailable_endpoint"
    )
    assert (
        perp_dex._provider_error_class_from_exception(
            httpx.HTTPStatusError("unavailable", request=request, response=unavailable)
        )
        == "provider_unavailable"
    )
    assert perp_dex._provider_error_class_from_exception(ValueError("bad json")) == "schema_drift"
    assert perp_dex._provider_error_class_from_snapshot({"status": "empty", "markets": []}) == "empty_response"
    assert (
        perp_dex._provider_error_class_from_snapshot(
            {"status": "empty", "markets": [], "reason": "missing_markets"}
        )
        == "schema_drift"
    )
