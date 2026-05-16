from typing import Optional

from app.adapters.base import BaseAdapter, RawTicker
from app.config import get_settings


class CoinGeckoService:
    """Service layer for CoinGecko data operations.

    Wraps the adapter and provides business-level operations.
    """

    def __init__(self, adapter: BaseAdapter):
        self.adapter = adapter
        self.settings = get_settings()

    async def fetch_spot_prices(self, instrument_ids: list[str]) -> list[RawTicker]:
        return await self.adapter.fetch_tickers(instrument_ids)

    async def health_check(self) -> dict:
        return await self.adapter.health_check()
