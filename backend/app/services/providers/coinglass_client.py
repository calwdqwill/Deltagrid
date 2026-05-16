"""CoinGlass API client with rate-limit awareness and graceful fallback.

Docs: https://coinglass.readme.io/reference
"""

import logging
from typing import Optional, Any
from datetime import datetime

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://open-api.coinglass.com"


class CoinGlassClient:
    """Rate-limit aware CoinGlass client with retry and fallback."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.coinglass_api_key
        self.base_url = (base_url or settings.coinglass_base_url).rstrip("/")
        self.client = httpx.AsyncClient(timeout=15.0, headers=self._headers())

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["coinglassSecret"] = self.api_key
        return headers

    async def close(self) -> None:
        await self.client.aclose()

    async def _request(self, method: str, path: str, **kwargs) -> Optional[dict]:
        if not self.api_key:
            logger.debug("CoinGlass API key not configured; skipping request")
            return None

        url = f"{self.base_url}{path}"
        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.warning(f"CoinGlass API error {e.response.status_code}: {e.response.text[:200]}")
            return None
        except Exception as e:
            logger.warning(f"CoinGlass request failed: {e}")
            return None

    async def get_funding_rates(self, symbol: Optional[str] = None) -> Optional[list[dict]]:
        """Fetch funding rates. Returns list of funding rate entries."""
        params = {}
        if symbol:
            params["symbol"] = symbol
        data = await self._request("GET", "/api/futures/fundingRate", params=params)
        if data and data.get("success"):
            return data.get("data", [])
        return None

    async def get_open_interest(self, symbol: Optional[str] = None) -> Optional[list[dict]]:
        """Fetch open interest."""
        params = {}
        if symbol:
            params["symbol"] = symbol
        data = await self._request("GET", "/api/futures/openInterest", params=params)
        if data and data.get("success"):
            return data.get("data", [])
        return None

    async def health_check(self) -> bool:
        """Quick health check."""
        if not self.api_key:
            return False
        data = await self._request("GET", "/api/futures/fundingRate")
        return data is not None
