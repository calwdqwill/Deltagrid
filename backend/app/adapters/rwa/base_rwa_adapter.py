"""Base adapter for RWA (Real World Assets) data providers."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class RwaAssetPayload:
    """Normalized payload from an RWA provider."""

    def __init__(
        self,
        symbol: str,
        name: str,
        category: str,
        price_usd: Optional[float] = None,
        nav_usd: Optional[float] = None,
        market_cap_usd: Optional[float] = None,
        total_supply: Optional[float] = None,
        volume_24h_usd: Optional[float] = None,
        yield_apr: Optional[float] = None,
        issuer: Optional[str] = None,
        blockchain: Optional[str] = None,
        contract_address: Optional[str] = None,
        raw_payload: Optional[dict] = None,
    ):
        self.symbol = symbol
        self.name = name
        self.category = category
        self.price_usd = price_usd
        self.nav_usd = nav_usd
        self.market_cap_usd = market_cap_usd
        self.total_supply = total_supply
        self.volume_24h_usd = volume_24h_usd
        self.yield_apr = yield_apr
        self.issuer = issuer
        self.blockchain = blockchain
        self.contract_address = contract_address
        self.raw_payload = raw_payload or {}


class BaseRwaAdapter(ABC):
    """Abstract base for RWA data adapters."""

    provider_name: str = "rwa_base"

    @abstractmethod
    async def fetch_asset(self, symbol: str) -> Optional[RwaAssetPayload]:
        """Fetch normalized data for a single RWA asset."""
        ...

    @abstractmethod
    async def fetch_all(self) -> list[RwaAssetPayload]:
        """Fetch normalized data for all supported RWA assets."""
        ...

    def get_expected_cadence_seconds(self) -> int:
        """Expected refresh cadence in seconds. Override per provider."""
        return 300
