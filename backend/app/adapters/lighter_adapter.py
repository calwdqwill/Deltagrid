from typing import Optional

from app.adapters.base import BaseAdapter, RawTicker
from app.adapters.coingecko_adapter import CoinGeckoAdapter


class LighterAdapter(BaseAdapter):
    """Lighter perp DEX adapter.

    Phase 1: Uses CoinGecko /exchanges/lighter/tickers as unified source.
    Phase 3: Will implement direct Lighter API calls.
    """

    source_name = "lighter"

    def __init__(self, cg_api_key: Optional[str] = None):
        self._cg = CoinGeckoAdapter(api_key=cg_api_key)

    async def fetch_tickers(self, instrument_ids: list[str]) -> list[RawTicker]:
        tickers = await self._cg.fetch_exchange_tickers("lighter", instrument_ids)
        for t in tickers:
            t.venue_id = "lighter"
            t.venue_name = "Lighter"
        return tickers

    async def health_check(self) -> dict:
        cg_health = await self._cg.health_check()
        return {
            "source": self.source_name,
            "status": cg_health.get("status", "unknown"),
            "mode": "coingecko_backed",
            "phase_3_direct_api": False,
            "last_success": cg_health.get("last_success"),
        }
