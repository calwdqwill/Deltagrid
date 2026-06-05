"""Regression tests for CoinGlass liquidation normalization."""

import pytest

from app.adapters.data.sync_market_data import _normalize_coinglass_liquidations


def test_coinglass_nested_turnover_maps_to_long_and_short_liquidations() -> None:
    rows = [
        {
            "ts": 1700000000000,
            "Binance": {
                "longTurnover": "1250.50",
                "shortTurnover": 340.25,
            },
        }
    ]

    normalized = _normalize_coinglass_liquidations("BTC", rows)

    assert len(normalized) == 2
    assert normalized[0].symbol == "BTC"
    assert normalized[0].exchange == "binance"
    assert normalized[0].side == "long"
    assert normalized[0].timestamp_ms == 1700000000000
    assert normalized[0].quantity == 0.0
    assert normalized[0].price == 0.0
    assert normalized[0].value_usd == pytest.approx(1250.50)
    assert normalized[1].side == "short"
    assert normalized[1].value_usd == pytest.approx(340.25)


def test_coinglass_root_camel_fields_accept_seconds_timestamp() -> None:
    rows = [
        {
            "time": 1700000000,
            "longLiquidationUsd": "0",
            "shortLiquidationUsd": "99.5",
        }
    ]

    normalized = _normalize_coinglass_liquidations("ETH", rows)

    assert len(normalized) == 1
    assert normalized[0].symbol == "ETH"
    assert normalized[0].side == "short"
    assert normalized[0].timestamp_ms == 1700000000000
    assert normalized[0].value_usd == pytest.approx(99.5)


def test_coinglass_root_aggregated_fields_match_v4_response() -> None:
    rows = [
        {
            "time": 1780657200000,
            "aggregated_long_liquidation_usd": 1668338.11546,
            "aggregated_short_liquidation_usd": "243395.6704",
        }
    ]

    normalized = _normalize_coinglass_liquidations("BTC", rows)

    assert len(normalized) == 2
    assert normalized[0].side == "long"
    assert normalized[0].value_usd == pytest.approx(1668338.11546)
    assert normalized[1].side == "short"
    assert normalized[1].value_usd == pytest.approx(243395.6704)


def test_coinglass_normalizer_skips_rows_without_timestamp_or_positive_value() -> None:
    rows = [
        {"Binance": {"longTurnover": "100"}},
        {"ts": 1700000000000, "Binance": {"longTurnover": 0, "shortTurnover": None}},
    ]

    normalized = _normalize_coinglass_liquidations("SOL", rows)

    assert normalized == []
