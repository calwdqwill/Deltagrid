import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1 import perp_dex
from app.services.providers.gmx_client import GmxClient


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def test_gmx_market_snapshot_preserves_raw_fixed_point_fields() -> None:
    fixture = _load_fixture("gmx_rate_fixture.json")

    snapshot = GmxClient.normalize_market_snapshot(
        fixture["markets_info"],
        symbols=("BTC",),
        token_payload=fixture["tokens"],
    )

    assert snapshot["status"] == "partial"
    assert snapshot["read_only"] is True
    assert snapshot["execution_enabled"] is False
    assert snapshot["normalization_status"] == "raw_fixed_point"
    assert snapshot["scale_validation_status"] == "token_decimals_resolved"
    assert snapshot["token_amount_scale_status"] == "pool_amounts_scaled"
    assert snapshot["diagnostic_usd_scale_status"] == "usd_diagnostics_scaled"
    assert snapshot["rate_semantics_status"] == "hourly_rate_relation_confirmed"
    assert snapshot["rate_source_fields_status"] == "source_factor_fields_unavailable"
    assert snapshot["rate_source_fields_summary"] == {
        "market_count": 1,
        "status_counts": {"source_factor_fields_unavailable": 1},
        "required_fields": [
            "fundingFactorPerSecond",
            "borrowingFactorPerSecondForLongs",
            "borrowingFactorPerSecondForShorts",
            "longsPayShorts",
        ],
        "present_fields": [],
        "missing_fields": [
            "borrowingFactorPerSecondForLongs",
            "borrowingFactorPerSecondForShorts",
            "fundingFactorPerSecond",
            "longsPayShorts",
        ],
    }
    assert snapshot["rate_relation_summary"] == {
        "market_count": 1,
        "side_count": 2,
        "status_counts": {"net_equals_funding_minus_borrowing": 2},
        "source_relation_match_side_count": 2,
        "raw_sum_relation_match_side_count": 0,
        "nonzero_borrowing_side_count": 2,
        "zero_borrowing_side_count": 0,
        "zero_borrowing_ambiguous_side_count": 0,
    }
    assert snapshot["token_metadata_source"] == "gmx_tokens"
    assert len(snapshot["markets"]) == 1

    market = snapshot["markets"][0]
    assert market["symbol"] == "BTC"
    assert market["market"] == "BTC/USD [WBTC.b-USDC]"
    assert market["venue_id"] == "gmx"
    assert market["status"] == "partial"
    assert market["provider_status"] == "listed"
    assert market["normalization_status"] == "raw_fixed_point"
    assert market["mark_price"] is None
    assert market["funding_pct"] is None
    assert market["open_interest_usd"] is None
    assert market["volume_24h_usd"] is None
    assert market["market_token"] == "0xbtc-market"
    assert market["index_token"] == "0xbtc"
    assert market["index_token_symbol"] == "BTC"
    assert market["index_token_decimals"] == 8
    assert market["index_token_synthetic"] is True
    assert market["long_token_symbol"] == "WBTC.b"
    assert market["long_token_decimals"] == 8
    assert market["short_token_symbol"] == "USDC"
    assert market["short_token_decimals"] == 6
    assert market["scale_validation_status"] == "token_decimals_resolved"
    assert market["pool_amount_long_token"] == "1"
    assert market["pool_amount_short_token"] == "200"
    assert market["token_amount_scale_status"] == "pool_amounts_scaled"
    assert market["open_interest_long_usd_diagnostic"] == "123456789"
    assert market["open_interest_short_usd_diagnostic"] == "234567890"
    assert market["available_liquidity_long_usd_diagnostic"] == "345678900"
    assert market["available_liquidity_short_usd_diagnostic"] == "456789000"
    assert market["diagnostic_usd_scale_status"] == "usd_diagnostics_scaled"
    assert market["diagnostic_usd_scale_decimals"] == 30
    assert market["diagnostic_usd_scale_source"] == "gmx_interface_market_ticker_usd_decimals"
    assert market["rate_semantics_status"] == "hourly_rate_relation_confirmed"
    assert market["rate_semantics_period"] == "1h"
    assert market["rate_semantics_source"] == "gmx_interface_market_ticker_hourly_rates"
    assert market["rate_source_fields_status"] == "source_factor_fields_unavailable"
    assert market["rate_source_fields_diagnostic"]["missing_fields"] == [
        "fundingFactorPerSecond",
        "borrowingFactorPerSecondForLongs",
        "borrowingFactorPerSecondForShorts",
        "longsPayShorts",
    ]
    assert "ticker rate outputs" in market["rate_source_fields_diagnostic"]["reason"]
    assert market["rate_relation_diagnostics"]["long"]["status"] == "net_equals_funding_minus_borrowing"
    assert market["rate_relation_diagnostics"]["long"]["source_expected_net"] == "122956789012345678"
    assert market["rate_relation_diagnostics"]["long"]["source_delta"] == "0"
    assert market["rate_relation_diagnostics"]["long"]["source_relation_matches"] is True
    assert market["rate_relation_diagnostics"]["long"]["raw_sum_relation_matches"] is False
    assert market["rate_relation_diagnostics"]["long"]["borrowing_is_zero"] is False
    assert market["rate_relation_diagnostics"]["long"]["zero_borrowing_relation_ambiguous"] is False
    assert market["rate_relation_diagnostics"]["short"]["status"] == "net_equals_funding_minus_borrowing"
    assert market["rate_relation_diagnostics"]["short"]["source_expected_net"] == "-124056789012345678"
    assert market["rate_relation_diagnostics"]["short"]["source_delta"] == "0"
    assert market["rate_relation_diagnostics"]["short"]["source_relation_matches"] is True
    assert market["rate_relation_diagnostics"]["short"]["raw_sum_relation_matches"] is False
    assert market["rate_relation_diagnostics"]["short"]["borrowing_is_zero"] is False
    assert market["rate_relation_diagnostics"]["short"]["zero_borrowing_relation_ambiguous"] is False
    assert market["raw_open_interest_long"] == "123456789000000000000000000000000000000"
    assert market["raw_available_liquidity_short"] == "456789000000000000000000000000000000000"
    assert market["raw_pool_amount_long"] == "100000000"
    assert market["raw_pool_amount_short"] == "200000000"
    assert market["raw_funding_rate_short"] == "-123456789012345678"
    assert market["raw_metrics"]["netRateShort"] == "-124056789012345678"
    assert market["resolution_action"] == "confirm_gmx_fixed_point_scales_and_token_decimals_before_using_liquidity_or_oi"


def test_gmx_market_endpoint_uses_read_only_stub_client() -> None:
    class StubGmxClient:
        async def fetch_market_snapshot(self, symbols: tuple[str, ...]) -> dict:
            return {
                "venue_id": "gmx",
                "status": "partial",
                "requested_symbols": list(symbols),
                "markets": [
                    {
                        "symbol": symbols[0],
                        "market": f"{symbols[0]}/USD [WBTC.b-USDC]",
                        "normalization_status": "raw_fixed_point",
                        "open_interest_usd": None,
                    }
                ],
                "read_only": True,
                "execution_enabled": False,
                "normalization_status": "raw_fixed_point",
                "scale_validation_status": "token_decimals_resolved",
                "token_amount_scale_status": "pool_amounts_scaled",
                "diagnostic_usd_scale_status": "usd_diagnostics_scaled",
                "rate_semantics_status": "hourly_rate_relation_confirmed",
                "rate_source_fields_status": "source_factor_fields_unavailable",
                "rate_source_fields_summary": {
                    "market_count": 1,
                    "status_counts": {"source_factor_fields_unavailable": 1},
                    "required_fields": [
                        "fundingFactorPerSecond",
                        "borrowingFactorPerSecondForLongs",
                        "borrowingFactorPerSecondForShorts",
                        "longsPayShorts",
                    ],
                    "present_fields": [],
                    "missing_fields": [
                        "borrowingFactorPerSecondForLongs",
                        "borrowingFactorPerSecondForShorts",
                        "fundingFactorPerSecond",
                        "longsPayShorts",
                    ],
                },
                "rate_relation_summary": {
                    "market_count": 1,
                    "side_count": 2,
                    "status_counts": {"net_equals_funding_minus_borrowing": 2},
                    "source_relation_match_side_count": 2,
                    "raw_sum_relation_match_side_count": 0,
                    "nonzero_borrowing_side_count": 2,
                    "zero_borrowing_side_count": 0,
                    "zero_borrowing_ambiguous_side_count": 0,
                },
            }

    async def stub_client():
        yield StubGmxClient()

    app = FastAPI()
    app.include_router(perp_dex.router, prefix="/api/v1")
    app.dependency_overrides[perp_dex.get_gmx_client] = stub_client

    client = TestClient(app)
    response = client.get("/api/v1/perp-dex/venues/gmx/markets?symbols=btc,ETH,btc")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["meta"]["read_only"] is True
    assert payload["meta"]["external_provider_calls"] is True
    assert payload["meta"]["source"] == "gmx"
    assert payload["meta"]["normalization_status"] == "raw_fixed_point"
    assert payload["meta"]["scale_validation_status"] == "token_decimals_resolved"
    assert payload["meta"]["token_amount_scale_status"] == "pool_amounts_scaled"
    assert payload["meta"]["diagnostic_usd_scale_status"] == "usd_diagnostics_scaled"
    assert payload["meta"]["rate_semantics_status"] == "hourly_rate_relation_confirmed"
    assert payload["meta"]["rate_source_fields_status"] == "source_factor_fields_unavailable"
    assert payload["meta"]["rate_relation_summary"]["status_counts"] == {"net_equals_funding_minus_borrowing": 2}
    assert payload["meta"]["requested_symbols"] == ["BTC", "ETH"]
    assert payload["data"]["token_amount_scale_status"] == "pool_amounts_scaled"
    assert payload["data"]["rate_semantics_status"] == "hourly_rate_relation_confirmed"
    assert payload["data"]["requested_symbols"] == ["BTC", "ETH"]
    assert payload["data"]["execution_enabled"] is False


def test_gmx_rate_relation_diagnostics_detect_observed_live_shape() -> None:
    fixture = _load_fixture("gmx_rate_live_shape_fixture.json")

    snapshot = GmxClient.normalize_market_snapshot(fixture["markets_info"], symbols=("ETH",))

    assert snapshot["rate_semantics_status"] == "raw_rate_relation_plus_with_zero_borrowing"
    assert snapshot["rate_source_fields_status"] == "source_factor_fields_unavailable"
    assert snapshot["rate_relation_summary"] == {
        "market_count": 1,
        "side_count": 2,
        "status_counts": {
            "net_equals_funding_plus_borrowing": 1,
            "net_equals_funding_with_zero_borrowing": 1,
        },
        "source_relation_match_side_count": 1,
        "raw_sum_relation_match_side_count": 2,
        "nonzero_borrowing_side_count": 1,
        "zero_borrowing_side_count": 1,
        "zero_borrowing_ambiguous_side_count": 1,
    }
    market = snapshot["markets"][0]
    assert market["rate_semantics_status"] == "raw_rate_relation_plus_with_zero_borrowing"
    assert market["funding_pct"] is None
    assert market["raw_funding_rate_long"] == "100"
    assert market["raw_net_rate_long"] == "107"
    long_relation = market["rate_relation_diagnostics"]["long"]
    assert long_relation["status"] == "net_equals_funding_plus_borrowing"
    assert long_relation["source_expected_net"] == "93"
    assert long_relation["source_delta"] == "14"
    assert long_relation["raw_sum_expected_net"] == "107"
    assert long_relation["raw_sum_delta"] == "0"
    assert long_relation["source_relation_matches"] is False
    assert long_relation["raw_sum_relation_matches"] is True
    assert long_relation["borrowing_is_zero"] is False
    assert long_relation["zero_borrowing_relation_ambiguous"] is False
    short_relation = market["rate_relation_diagnostics"]["short"]
    assert short_relation["status"] == "net_equals_funding_with_zero_borrowing"
    assert short_relation["source_delta"] == "0"
    assert short_relation["raw_sum_delta"] == "0"
    assert short_relation["source_relation_matches"] is True
    assert short_relation["raw_sum_relation_matches"] is True
    assert short_relation["borrowing_is_zero"] is True
    assert short_relation["zero_borrowing_relation_ambiguous"] is True
