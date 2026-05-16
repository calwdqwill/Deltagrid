from typing import Optional

from app.adapters.base import BaseAdapter, RawTicker
from app.adapters.coingecko_adapter import CoinGeckoAdapter


class AsterAdapter(BaseAdapter):
    """Aster perp DEX adapter.

    Phase 1: Uses CoinGecko /exchanges/aster-futures/tickers as unified source.
    Phase 3: Will implement direct Aster API calls.
    """

    source_name = "aster"

    def __init__(self, cg_api_key: Optional[str] = None):
        self._cg = CoinGeckoAdapter(api_key=cg_api_key)

    async def fetch_tickers(self, instrument_ids: list[str]) -> list[RawTicker]:
        tickers = await self._cg.fetch_exchange_tickers("aster-futures", instrument_ids)
        for t in tickers:
            t.venue_id = "aster"
            t.venue_name = "Aster"
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
