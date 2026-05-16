from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class RawTicker:
    instrument_id: str
    symbol: str
    venue_id: str
    venue_name: str
    price: float
    volume_24h: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    funding_rate: Optional[float] = None
    open_interest: Optional[float] = None
    timestamp: Optional[str] = None


class BaseAdapter(ABC):
    """Abstract base for all data source adapters.

    Future-proofing: new exchanges/DEXes implement this protocol.
    Phase 1: CoinGeckoAdapter is primary. Perp DEX adapters use CG-backed data.
    Phase 3: Direct API implementations replace CG-backed stubs.
    """

    source_name: str = "unknown"

    @abstractmethod
    async def fetch_tickers(self, instrument_ids: list[str]) -> list[RawTicker]:
        """Fetch tickers for given instrument IDs."""
        ...

    @abstractmethod
    async def health_check(self) -> dict:
        """Return adapter health status."""
        ...
