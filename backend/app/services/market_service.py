from datetime import datetime
from typing import Optional

import httpx

from app.adapters.coingecko_adapter import CoinGeckoAdapter
from app.config import get_settings
from app.services.cache_service import InMemoryCacheService
from app.services.providers.coinglass_client import CoinGlassClient
from app.services.providers.geckoterminal_client import GeckoTerminalClient


async def fetch_fear_greed(limit: int = 7) -> list[dict]:
    """Fetch Fear & Greed Index from alternative.me API."""
    url = f"https://api.alternative.me/fng/?limit={limit}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers={"Accept": "application/json"})
            if resp.status_code == 200:
                data = resp.json()
                return [
                    {
                        "value": int(item["value"]),
                        "classification": item["value_classification"],
                        "timestamp": int(item["timestamp"]),
                        "time_until_update": int(item.get("time_until_update", 0)),
                    }
                    for item in data.get("data", [])
                ]
    except Exception:
        pass
    return []


class MarketService:
    """Service for market overview data (trending, gainers, losers, global stats, fear & greed)."""

    CACHE_KEYS = {
        "trending": "market_trending",
        "global": "market_global",
        "markets": "market_markets",
        "fear_greed": "market_fear_greed",
    }

    def __init__(self, cache: Optional[InMemoryCacheService] = None):
        self.adapter = CoinGeckoAdapter()
        self.cache = cache or InMemoryCacheService(
            max_size=get_settings().cache_max_size,
            default_ttl=get_settings().cache_ttl_seconds,
        )

    async def get_trending(self) -> list[dict]:
        cached = await self.cache.get(self.CACHE_KEYS["trending"])
        if cached:
            return cached
        data = await self.adapter.fetch_trending()
        await self.cache.set(self.CACHE_KEYS["trending"], data, 60)
        return data

    async def get_global(self) -> dict:
        cached = await self.cache.get(self.CACHE_KEYS["global"])
        if cached:
            return cached
        data = await self.adapter.fetch_global()
        data["updated_at"] = datetime.utcnow().isoformat()
        await self.cache.set(self.CACHE_KEYS["global"], data, 60)
        return data

    async def get_markets(self, limit: int = 20) -> list[dict]:
        """Fetch top spot markets with 24h/7d change."""
        normalized_limit = max(1, min(limit, 100))
        cache_key = f"{self.CACHE_KEYS['markets']}:{normalized_limit}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        data = await self.adapter.fetch_markets(
            order="market_cap_desc",
            per_page=normalized_limit,
            price_change="24h,7d",
        )
        await self.cache.set(cache_key, data, 60)
        return data

    async def _get_markets(self) -> list[dict]:
        """Fetch top markets with 24h change — shared cache for gainers/losers."""
        data = await self.get_markets(limit=20)
        return data

    async def get_gainers(self, limit: int = 5) -> list[dict]:
        data = await self._get_markets()
        gainers = sorted(
            [c for c in data if (c.get("price_change_percentage_24h") or 0) > 0],
            key=lambda x: x.get("price_change_percentage_24h") or 0,
            reverse=True,
        )[:limit]
        return gainers

    async def get_losers(self, limit: int = 5) -> list[dict]:
        data = await self._get_markets()
        losers = sorted(
            [c for c in data if (c.get("price_change_percentage_24h") or 0) < 0],
            key=lambda x: x.get("price_change_percentage_24h") or 0,
            reverse=False,
        )[:limit]
        return losers

    async def get_fear_greed(self, limit: int = 7) -> list[dict]:
        cached = await self.cache.get(self.CACHE_KEYS["fear_greed"])
        if cached:
            return cached
        data = await fetch_fear_greed(limit)
        await self.cache.set(self.CACHE_KEYS["fear_greed"], data, 3600)
        return data

    async def get_new_listings(self, limit: int = 10) -> list[dict]:
        """Return trending coins with highest market_cap_rank (smallest/newest)."""
        data = await self.get_trending()
        # Sort by market_cap_rank descending — highest rank = smallest/newest
        new_coins = sorted(
            [c for c in data if c.get("market_cap_rank")],
            key=lambda x: x.get("market_cap_rank") or 0,
            reverse=True,
        )[:limit]
        return new_coins

    async def get_funding_rates(self) -> list[dict]:
        """Fetch funding rates from CoinGlass with fallback to placeholder."""
        client = CoinGlassClient()
        try:
            rates = await client.get_funding_rates()
            if rates:
                # Normalize CoinGlass data to our schema
                normalized = []
                for item in rates[:10]:
                    rate = (
                        item.get("fundingRate")
                        or item.get("funding_rate")
                        or item.get("avg_funding_rate_by_oi")
                        or item.get("avg_funding_rate_by_vol")
                        or 0
                    )
                    annualized = item.get("fundingRateAnnualized")
                    if annualized is None:
                        annualized = float(rate or 0) * 3 * 365
                    normalized.append({
                        "symbol": item.get("symbol", "UNKNOWN"),
                        "rate": rate,
                        "interval": item.get("interval", "8h"),
                        "exchange": item.get("exchange", "CoinGlass"),
                        "annualized": annualized,
                        "open_interest_usd": item.get("open_interest_usd"),
                        "price": item.get("current_price"),
                        "data_status": "live",
                    })
                return normalized
        except Exception:
            pass
        finally:
            await client.close()

        # Fallback: placeholder data with explicit flag
        return [
            {"symbol": "BTC", "rate": 0.0102, "interval": "8h", "exchange": "Binance", "annualized": 11.2, "data_status": "fallback"},
            {"symbol": "ETH", "rate": 0.0085, "interval": "8h", "exchange": "Binance", "annualized": 9.3, "data_status": "fallback"},
            {"symbol": "SOL", "rate": 0.0156, "interval": "8h", "exchange": "Binance", "annualized": 17.1, "data_status": "fallback"},
            {"symbol": "XRP", "rate": 0.0221, "interval": "8h", "exchange": "Binance", "annualized": 24.2, "data_status": "fallback"},
            {"symbol": "DOGE", "rate": 0.0315, "interval": "8h", "exchange": "Binance", "annualized": 34.5, "data_status": "fallback"},
            {"symbol": "HYPE", "rate": 0.0450, "interval": "8h", "exchange": "Hyperliquid", "annualized": 49.3, "data_status": "fallback"},
            {"symbol": "LINK", "rate": 0.0128, "interval": "8h", "exchange": "Binance", "annualized": 14.0, "data_status": "fallback"},
            {"symbol": "SUI", "rate": 0.0189, "interval": "8h", "exchange": "Binance", "annualized": 20.7, "data_status": "fallback"},
        ]
