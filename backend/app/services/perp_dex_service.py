from typing import Optional

from app.adapters.base import BaseAdapter, RawTicker
from app.adapters.registry import AdapterRegistry


class PerpDEXService:
    """Service layer for Perp DEX data aggregation.

    Aggregates tickers from multiple perp DEX adapters via registry.
    Phase 1: Uses CG-backed adapters. Phase 3: Direct APIs.
    """

    def __init__(self, registry: AdapterRegistry):
        self.registry = registry

    async def fetch_perp_prices(self, instrument_ids: list[str]) -> list[RawTicker]:
        all_tickers: list[RawTicker] = []
        for name in ["hyperliquid", "aster", "lighter"]:
            adapter = self.registry.get(name)
            if adapter:
                try:
                    tickers = await adapter.fetch_tickers(instrument_ids)
                    all_tickers.extend(tickers)
                except Exception:
                    continue
        return all_tickers

    async def health_check(self) -> dict:
        return await self.registry.health_check_all()
