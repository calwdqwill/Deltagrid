"""Regression tests for CoinGlass Perp DEX enrichment normalization."""

import pytest

from app.services.providers.coinglass_client import CoinGlassClient


def test_coinglass_perp_dex_normalizer_keeps_rows_research_only() -> None:
    snapshot = CoinGlassClient.normalize_perp_dex_market_snapshot(
        rows_by_exchange={
            "Aster": [
                {
                    "symbol": "BTC",
                    "current_price": "65000.5",
                    "avg_funding_rate_by_oi": "0.0123",
                    "open_interest_usd": "1234567.89",
                    "open_interest_quantity": "18.25",
                    "longShortRatio1h": "1.234",
                    "longLiquidationUsd24h": "1000",
                    "shortLiquidationUsd24h": "250",
                    "open_interest_change_percent_24h": "-2.5",
                }
            ],
        },
        symbols=("BTC", "ETH"),
        exchanges=("Aster", "Lighter"),
        fetched_at="2026-06-17T00:00:00+00:00",
        errors={"Lighter": "no_data_returned"},
    )

    assert snapshot["status"] == "partial"
    assert snapshot["read_only"] is True
    assert snapshot["execution_enabled"] is False
    assert snapshot["ranking_enabled"] is False
    assert snapshot["production_signal_enabled"] is False
    assert snapshot["normalization_status"] == "coinglass_coin_market_enrichment"
    assert snapshot["errors"] == {"Lighter": "no_data_returned"}
    assert snapshot["coverage_summary"]["total_rows"] == 1
    assert snapshot["coverage_summary"]["exchanges_with_matches"] == 1
    assert snapshot["coverage_summary"]["direct_adapter_candidate_hints"] == ["Aster"]
    assert snapshot["coverage_summary"]["field_totals"]["funding"] == 1
    assert snapshot["coverage_summary"]["field_totals"]["open_interest"] == 1
    assert snapshot["coverage_summary"]["field_totals"]["long_short"] == 1
    assert snapshot["coverage_summary"]["by_exchange"]["Aster"]["status"] == "partial"
    assert snapshot["coverage_summary"]["by_exchange"]["Aster"]["matched_symbols"] == ["BTC"]
    assert snapshot["coverage_summary"]["by_exchange"]["Aster"]["missing_symbols"] == ["ETH"]
    assert snapshot["coverage_summary"]["by_exchange"]["Aster"]["route_input_status"] == "not_route_input"
    assert snapshot["coverage_summary"]["by_exchange"]["Lighter"]["status"] == "request_failed"

    assert len(snapshot["markets"]) == 1
    row = snapshot["markets"][0]
    assert row["venue_id"] == "coinglass:aster"
    assert row["venue_name"] == "Aster"
    assert row["status"] == "partial"
    assert row["provider_status"] == "third_party_aggregate"
    assert row["mark_price"] == pytest.approx(65000.5)
    assert row["funding_pct"] == pytest.approx(0.0123)
    assert row["funding_rate"] == pytest.approx(0.000123)
    assert row["open_interest_usd"] == pytest.approx(1234567.89)
    assert row["open_interest_base"] == pytest.approx(18.25)
    assert row["long_short_ratio_1h"] == pytest.approx(1.234)
    assert row["long_liquidation_usd_24h"] == pytest.approx(1000)
    assert row["short_liquidation_usd_24h"] == pytest.approx(250)
    assert row["source_endpoint"] == "/api/futures/coins-markets"
    assert "not execution-grade" in row["resolution_reason"]


def test_coinglass_perp_dex_normalizer_reports_unavailable_when_all_requests_fail() -> None:
    snapshot = CoinGlassClient.normalize_perp_dex_market_snapshot(
        rows_by_exchange={},
        symbols=("BTC",),
        exchanges=("Aster",),
        fetched_at="2026-06-17T00:00:00+00:00",
        errors={"Aster": "no_data_returned"},
    )

    assert snapshot["status"] == "unavailable"
    assert snapshot["markets"] == []
    assert snapshot["reason"] == "all_exchange_requests_failed"
    assert snapshot["coverage_summary"]["total_rows"] == 0
    assert snapshot["coverage_summary"]["by_exchange"]["Aster"]["status"] == "request_failed"
