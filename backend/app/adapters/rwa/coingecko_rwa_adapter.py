"""CoinGecko adapter for RWA assets (XAUT, PAXG, etc.)."""

import logging
from datetime import datetime
from typing import Optional

import httpx

from app.adapters.rwa.base_rwa_adapter import BaseRwaAdapter, RwaAssetPayload
from app.config import get_settings

logger = logging.getLogger(__name__)


class CoinGeckoRwaAdapter(BaseRwaAdapter):
    """Fetch RWA asset data from CoinGecko API.

    Maps:
      - XAUT -> tether-gold
      - PAXG -> pax-gold
    """

    provider_name = "coingecko_rwa"

    COIN_ID_MAP = {
        "XAUT": "tether-gold",
        "PAXG": "pax-gold",
    }

    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.coingecko_api_key
        self.base_url = (
            settings.coingecko_pro_base_url
            if self.api_key
            else settings.coingecko_demo_base_url
        )
        self.client = httpx.AsyncClient(timeout=15.0)
        self._last_success: Optional[datetime] = None
        self._last_error: Optional[str] = None

    def _headers(self) -> dict:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["x-cg-pro-api-key"] = self.api_key
        return headers

    def _params(self) -> dict:
        params = {}
        if self.api_key:
            params["x_cg_pro_api_key"] = self.api_key
        return params

    async def fetch_asset(self, symbol: str) -> Optional[RwaAssetPayload]:
        coin_id = self.COIN_ID_MAP.get(symbol.upper())
        if not coin_id:
            logger.warning("Unknown RWA symbol for CoinGecko: %s", symbol)
            return None

        url = f"{self.base_url}/coins/{coin_id}"
        params = self._params()
        params.update({
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
        })

        try:
            resp = await self.client.get(url, headers=self._headers(), params=params)
            if resp.status_code in (429, 401, 404):
                self._last_error = f"HTTP {resp.status_code}"
                return None
            resp.raise_for_status()
            data = resp.json()
            self._last_success = datetime.utcnow()
            self._last_error = None
            return self._normalize(data, symbol)
        except Exception as e:
            self._last_error = str(e)
            logger.exception("CoinGecko RWA fetch failed for %s", symbol)
            return None

    async def fetch_all(self) -> list[RwaAssetPayload]:
        results = []
        for symbol in self.COIN_ID_MAP:
            payload = await self.fetch_asset(symbol)
            if payload:
                results.append(payload)
        return results

    def _normalize(self, data: dict, symbol: str) -> RwaAssetPayload:
        market_data = data.get("market_data", {})
        current_price = market_data.get("current_price", {})
        market_cap = market_data.get("market_cap", {})
        total_supply = market_data.get("total_supply")
        volume_24h = market_data.get("total_volume", {})

        return RwaAssetPayload(
            symbol=symbol.upper(),
            name=data.get("name", symbol),
            category="tokenized_gold",
            price_usd=current_price.get("usd"),
            market_cap_usd=market_cap.get("usd"),
            total_supply=total_supply,
            volume_24h_usd=volume_24h.get("usd"),
            issuer=data.get("asset_platform_id"),  # e.g. "ethereum"
            blockchain=data.get("asset_platform_id"),
            contract_address=data.get("contract_address"),
            raw_payload=data,
        )

    async def close(self):
        await self.client.aclose()
