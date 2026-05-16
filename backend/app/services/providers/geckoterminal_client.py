"""GeckoTerminal API client with pagination and graceful fallback.

Docs: https://api.geckoterminal.com/api/v2
"""

import logging
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.geckoterminal.com/api/v2"


class GeckoTerminalClient:
    """Rate-limit aware GeckoTerminal client."""

    def __init__(self, base_url: Optional[str] = None):
        settings = get_settings()
        self.base_url = (base_url or settings.geckoterminal_base_url).rstrip("/")
        self.client = httpx.AsyncClient(timeout=15.0)

    async def close(self) -> None:
        await self.client.aclose()

    async def _request(self, method: str, path: str, **kwargs) -> Optional[dict]:
        url = f"{self.base_url}{path}"
        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.warning(f"GeckoTerminal API error {e.response.status_code}: {e.response.text[:200]}")
            return None
        except Exception as e:
            logger.warning(f"GeckoTerminal request failed: {e}")
            return None

    async def get_pools(self, network: str = "eth", page: int = 1) -> Optional[list[dict]]:
        """Fetch top pools by network."""
        data = await self._request("GET", f"/networks/{network}/pools", params={"page": page})
        if data:
            return data.get("data", [])
        return None

    async def get_pool_ohlcv(self, network: str, pool_address: str, timeframe: str = "day") -> Optional[dict]:
        """Fetch OHLCV for a pool."""
        data = await self._request("GET", f"/networks/{network}/pools/{pool_address}/ohlcv/{timeframe}")
        if data:
            return data.get("data", {})
        return None

    async def health_check(self) -> bool:
        """Quick health check using ETH network pools."""
        data = await self._request("GET", "/networks/eth/pools", params={"page": 1})
        return data is not None
