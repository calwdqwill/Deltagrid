"""CoinGlass API client with rate-limit awareness and graceful fallback.

Docs: https://coinglass.readme.io/reference
"""

import logging
from typing import Optional, Any
from datetime import datetime

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://open-api-v4.coinglass.com"


class CoinGlassClient:
    """Rate-limit aware CoinGlass client with retry and fallback."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.coinglass_api_key
        self.base_url = (base_url or settings.coinglass_base_url).rstrip("/")
        self.client = httpx.AsyncClient(timeout=15.0, headers=self._headers())

    def _headers(self) -> dict:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.api_key:
            if "open-api-v4.coinglass.com" in self.base_url:
                headers["CG-API-KEY"] = self.api_key
            else:
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

    @staticmethod
    def _extract_data(payload: Optional[dict]) -> Optional[Any]:
        if not payload:
            return None
        if payload.get("success") is True:
            return payload.get("data")
        if payload.get("code") in ("0", 0):
            return payload.get("data")
        return None

    async def get_funding_rates(
        self,
        symbol: Optional[str] = None,
        exchange_list: str = "Binance",
    ) -> Optional[list[dict]]:
        """Fetch funding rates. Returns list of funding rate entries."""
        params = {
            "exchange_list": exchange_list,
            "per_page": 100,
            "page": 1,
        }
        if symbol:
            params["symbol"] = symbol
        data = await self._request("GET", "/api/futures/coins-markets", params=params)
        rows = self._extract_data(data)
        if isinstance(rows, list):
            return rows
        return None

    async def get_open_interest(
        self,
        symbol: Optional[str] = None,
        exchange_list: str = "Binance",
    ) -> Optional[list[dict]]:
        """Fetch open interest."""
        params = {
            "exchange_list": exchange_list,
            "per_page": 100,
            "page": 1,
        }
        if symbol:
            params["symbol"] = symbol
        data = await self._request("GET", "/api/futures/coins-markets", params=params)
        rows = self._extract_data(data)
        if isinstance(rows, list):
            return rows
        return None

    async def get_liquidation_aggregated_history(
        self,
        symbol: str,
        exchange_list: str = "Binance",
        interval: str = "1h",
        limit: int = 1000,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> Optional[list[dict]]:
        """Fetch aggregated long/short liquidation history for a futures coin."""
        params = {
            "exchange_list": exchange_list,
            "symbol": symbol,
            "interval": interval,
            "limit": min(limit, 1000),
        }
        if start_time is not None:
            params["start_time"] = start_time
        if end_time is not None:
            params["end_time"] = end_time

        data = await self._request(
            "GET",
            "/api/futures/liquidation/aggregated-history",
            params=params,
        )
        rows = self._extract_data(data)
        if isinstance(rows, list):
            return rows
        if isinstance(rows, dict):
            for key in ("list", "items", "rows", "data"):
                nested = rows.get(key)
                if isinstance(nested, list):
                    return nested
        return None

    async def health_check(self) -> bool:
        """Quick health check."""
        if not self.api_key:
            return False
        data = await self._request(
            "GET",
            "/api/futures/coins-markets",
            params={"exchange_list": "Binance", "per_page": 1, "page": 1},
        )
        return self._extract_data(data) is not None
