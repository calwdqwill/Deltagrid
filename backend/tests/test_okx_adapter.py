"""Regression tests for OKX market data normalization."""

import asyncio

import httpx
import pytest

from app.adapters.data.okx_adapter import OkxAdapter
from app.adapters.data.rate_limiter import GlobalRateLimiter, RateLimitExceeded, RetryPolicy


class _FakeRateLimitedClient:
    async def get(self, url: str, params: dict | None = None):
        request = httpx.Request("GET", url, params=params)
        return httpx.Response(429, headers={"Retry-After": "2"}, request=request)


def test_okx_interval_mapping_uses_uppercase_hours() -> None:
    assert OkxAdapter._to_okx_bar("1m") == "1m"
    assert OkxAdapter._to_okx_bar("5m") == "5m"
    assert OkxAdapter._to_okx_bar("1h") == "1H"
    assert OkxAdapter._to_okx_bar("1d") == "1D"


def test_okx_http_429_is_classified_as_rate_limit() -> None:
    async def _run() -> None:
        adapter = OkxAdapter(
            rate_limiter=GlobalRateLimiter(),
            retry_policy=RetryPolicy(max_retries=0),
        )
        await adapter.client.aclose()
        adapter.client = _FakeRateLimitedClient()

        with pytest.raises(RateLimitExceeded) as exc_info:
            await adapter._get_okx_data("https://www.okx.com/api/v5/test", {})

        assert "OKX rate limit exceeded" in str(exc_info.value)
        assert "retry_after=2" in str(exc_info.value)

    asyncio.run(_run())


def test_okx_candle_normalization_uses_base_and_quote_volume() -> None:
    row = [
        "1781305920000",
        "63439.1",
        "63439.1",
        "63415.6",
        "63415.6",
        "846.61",
        "8.4661",
        "536987.53618",
        "1",
    ]

    candle = OkxAdapter._normalize_candle(row, "BTC", "1m")

    assert candle.timestamp_ms == 1781305920000
    assert candle.symbol == "BTC"
    assert candle.exchange == "okx"
    assert candle.interval == "1m"
    assert candle.open == pytest.approx(63439.1)
    assert candle.close == pytest.approx(63415.6)
    assert candle.volume == pytest.approx(8.4661)
    assert candle.quote_volume == pytest.approx(536987.53618)


def test_okx_funding_normalization_prefers_realized_rate() -> None:
    row = {
        "fundingRate": "-0.0000200000000000",
        "fundingTime": "1781280000000",
        "instId": "BTC-USDT-SWAP",
        "realizedRate": "-0.0000223589457138",
    }

    funding = OkxAdapter._normalize_funding(row, "BTC")

    assert funding.timestamp_ms == 1781280000000
    assert funding.symbol == "BTC"
    assert funding.exchange == "okx"
    assert funding.interval == "8h"
    assert funding.funding_rate == pytest.approx(-0.0000223589457138)
    assert funding.next_funding_time_ms == 1781308800000


def test_okx_open_interest_normalization_maps_usd_and_coin_values() -> None:
    row = {
        "instId": "BTC-USDT-SWAP",
        "oi": "2937085.3500000068",
        "oiCcy": "29370.853500000068",
        "oiUsd": "1862819949.4693543128388",
        "ts": "1781306015444",
    }

    oi = OkxAdapter._normalize_open_interest(row, "BTC", "snapshot")

    assert oi.timestamp_ms == 1781306015444
    assert oi.symbol == "BTC"
    assert oi.exchange == "okx"
    assert oi.interval == "snapshot"
    assert oi.oi_usd == pytest.approx(1862819949.4693543)
    assert oi.oi_coins == pytest.approx(29370.853500000068)


def test_okx_long_short_ratio_is_converted_to_account_shares() -> None:
    ratio = OkxAdapter._normalize_long_short(["1781305200000", "1.47"], "BTC", "1h")

    assert ratio.timestamp_ms == 1781305200000
    assert ratio.symbol == "BTC"
    assert ratio.exchange == "okx"
    assert ratio.interval == "1h"
    assert ratio.long_account_ratio == pytest.approx(1.47 / 2.47)
    assert ratio.short_account_ratio == pytest.approx(1 / 2.47)
