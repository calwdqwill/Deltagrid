import asyncio
from datetime import datetime
from typing import Optional

import httpx

from app.adapters.base import BaseAdapter, RawTicker
from app.config import get_settings
from app.constants import DEFAULT_EXCHANGES, DEFAULT_INSTRUMENTS, MOCK_PERP_PRICES, MOCK_SPOT_PRICES, MOCK_VOLUMES


class CoinGeckoAdapter(BaseAdapter):
    """CoinGecko API adapter for spot and exchange ticker data.

    Phase 1: Uses Demo or Pro endpoints based on API key presence.
    Handles rate limits, retries, and fallback to mock data.
    """

    source_name = "coingecko"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_settings().coingecko_api_key
        self.base_url = (
            get_settings().coingecko_pro_base_url
            if self.api_key
            else get_settings().coingecko_demo_base_url
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
        return {}

    async def fetch_tickers(self, instrument_ids: list[str]) -> list[RawTicker]:
        """Fetch spot prices for instruments via /simple/price."""
        if not instrument_ids:
            return []

        ids_str = ",".join(instrument_ids)
        url = f"{self.base_url}/simple/price"
        params = self._params()
        params.update({
            "ids": ids_str,
            "vs_currencies": "usd",
            "include_24hr_vol": "true",
            "include_last_updated_at": "true",
        })

        try:
            resp = await self.client.get(url, headers=self._headers(), params=params)
            if resp.status_code == 429:
                self._last_error = "Rate limited"
                return self._mock_tickers(instrument_ids, reason="rate_limited")
            if resp.status_code == 401:
                self._last_error = "Unauthorized"
                return self._mock_tickers(instrument_ids, reason="unauthorized")
            resp.raise_for_status()
            data = resp.json()
            self._last_success = datetime.utcnow()
            self._last_error = None
            return self._normalize(data, instrument_ids)
        except httpx.HTTPError as e:
            self._last_error = str(e)
            return self._mock_tickers(instrument_ids, reason=f"http_error: {e}")
        except Exception as e:
            self._last_error = str(e)
            return self._mock_tickers(instrument_ids, reason=f"exception: {e}")

    async def fetch_exchange_tickers(self, exchange_id: str, instrument_ids: list[str]) -> list[RawTicker]:
        """Fetch exchange-specific tickers via /exchanges/{id}/tickers."""
        url = f"{self.base_url}/exchanges/{exchange_id}/tickers"
        params = self._params()
        params.update({"coin_ids": ",".join(instrument_ids)})

        try:
            resp = await self.client.get(url, headers=self._headers(), params=params)
            if resp.status_code in (429, 401, 404):
                return self._mock_exchange_tickers(exchange_id, instrument_ids)
            resp.raise_for_status()
            data = resp.json()
            self._last_success = datetime.utcnow()
            return self._normalize_exchange(data, exchange_id, instrument_ids)
        except Exception:
            return self._mock_exchange_tickers(exchange_id, instrument_ids)

    def _normalize(self, data: dict, instrument_ids: list[str]) -> list[RawTicker]:
        tickers = []
        for inst_id in instrument_ids:
            info = DEFAULT_INSTRUMENTS.get(inst_id, {})
            inst_data = data.get(inst_id, {})
            usd = inst_data.get("usd")
            if usd is None:
                continue
            tickers.append(RawTicker(
                instrument_id=inst_id,
                symbol=info.get("symbol", inst_id.upper()),
                venue_id="coingecko_aggregated",
                venue_name="CoinGecko",
                price=float(usd),
                volume_24h=inst_data.get("usd_24h_vol"),
                timestamp=str(datetime.utcnow()),
            ))
        return tickers

    def _normalize_exchange(self, data: dict, exchange_id: str, instrument_ids: list[str]) -> list[RawTicker]:
        tickers = []
        exchange_info = DEFAULT_EXCHANGES.get(exchange_id, {"name": exchange_id})
        tickers_data = data.get("tickers", [])
        symbol_to_id = {v["symbol"].upper(): k for k, v in DEFAULT_INSTRUMENTS.items()}

        for t in tickers_data:
            target = t.get("target", "").upper()
            if target != "USD" and target != "USDT":
                continue
            symbol = t.get("base", "").upper()
            inst_id = symbol_to_id.get(symbol)
            if inst_id is None or inst_id not in instrument_ids:
                continue
            tickers.append(RawTicker(
                instrument_id=inst_id,
                symbol=symbol,
                venue_id=exchange_id,
                venue_name=exchange_info["name"],
                price=t.get("last"),
                volume_24h=t.get("converted_volume", {}).get("usd"),
                bid=t.get("bid"),
                ask=t.get("ask"),
                timestamp=str(datetime.utcnow()),
            ))
        return tickers

    def _mock_tickers(self, instrument_ids: list[str], reason: str = "fallback") -> list[RawTicker]:
        tickers = []
        for inst_id in instrument_ids:
            info = DEFAULT_INSTRUMENTS.get(inst_id, {})
            symbol = info.get("symbol", inst_id.upper())
            prices = MOCK_SPOT_PRICES.get(inst_id, {})
            for venue, price in prices.items():
                tickers.append(RawTicker(
                    instrument_id=inst_id,
                    symbol=symbol,
                    venue_id=venue,
                    venue_name=DEFAULT_EXCHANGES.get(venue, {}).get("name", venue),
                    price=price,
                    volume_24h=MOCK_VOLUMES.get(inst_id),
                    timestamp=str(datetime.utcnow()),
                ))
        return tickers

    def _mock_exchange_tickers(self, exchange_id: str, instrument_ids: list[str]) -> list[RawTicker]:
        tickers = []
        exchange_info = DEFAULT_EXCHANGES.get(exchange_id, {"name": exchange_id})
        for inst_id in instrument_ids:
            info = DEFAULT_INSTRUMENTS.get(inst_id, {})
            symbol = info.get("symbol", inst_id.upper())
            price = MOCK_PERP_PRICES.get(inst_id, {}).get(exchange_id)
            if price is None:
                continue
            tickers.append(RawTicker(
                instrument_id=inst_id,
                symbol=symbol,
                venue_id=exchange_id,
                venue_name=exchange_info["name"],
                price=price,
                volume_24h=MOCK_VOLUMES.get(inst_id),
                timestamp=str(datetime.utcnow()),
            ))
        return tickers

    async def fetch_trending(self) -> list[dict]:
        """Fetch trending coins via /search/trending."""
        url = f"{self.base_url}/search/trending"
        try:
            resp = await self.client.get(url, headers=self._headers(), params=self._params())
            resp.raise_for_status()
            data = resp.json()
            coins = data.get("coins", [])
            return [
                {
                    "id": c["item"]["id"],
                    "name": c["item"]["name"],
                    "symbol": c["item"]["symbol"],
                    "market_cap_rank": c["item"].get("market_cap_rank"),
                    "thumb": c["item"].get("thumb"),
                    "price_btc": c["item"].get("price_btc"),
                    "score": c["item"].get("score", 0),
                }
                for c in coins
            ]
        except httpx.HTTPError as e:
            self._last_error = str(e)
            return []

    async def fetch_global(self) -> dict:
        """Fetch global crypto market data via /global."""
        url = f"{self.base_url}/global"
        try:
            resp = await self.client.get(url, headers=self._headers(), params=self._params())
            resp.raise_for_status()
            data = resp.json().get("data", {})
            return {
                "total_market_cap_usd": data.get("total_market_cap", {}).get("usd", 0),
                "total_volume_24h_usd": data.get("total_volume", {}).get("usd", 0),
                "btc_dominance": data.get("market_cap_percentage", {}).get("btc", 0),
                "eth_dominance": data.get("market_cap_percentage", {}).get("eth", 0),
                "active_cryptocurrencies": data.get("active_cryptocurrencies", 0),
            }
        except httpx.HTTPError as e:
            self._last_error = str(e)
            return {}

    async def fetch_markets(self, order: str = "market_cap_desc", per_page: int = 5, price_change: str = "24h") -> list[dict]:
        """Fetch coin markets via /coins/markets."""
        url = f"{self.base_url}/coins/markets"
        params = self._params()
        params.update({
            "vs_currency": "usd",
            "order": order,
            "per_page": per_page,
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": price_change,
        })
        try:
            resp = await self.client.get(url, headers=self._headers(), params=params)
            resp.raise_for_status()
            data = resp.json()
            return [
                {
                    "id": c["id"],
                    "name": c["name"],
                    "symbol": c["symbol"],
                    "image": c.get("image"),
                    "current_price": c.get("current_price"),
                    "market_cap": c.get("market_cap"),
                    "market_cap_rank": c.get("market_cap_rank"),
                    "price_change_percentage_24h": c.get("price_change_percentage_24h"),
                    "total_volume": c.get("total_volume"),
                }
                for c in data
            ]
        except httpx.HTTPError as e:
            self._last_error = str(e)
            return []

    async def health_check(self) -> dict:
        return {
            "source": self.source_name,
            "status": "ok" if self._last_success else "degraded",
            "last_success": self._last_success.isoformat() if self._last_success else None,
            "last_error": self._last_error,
            "has_api_key": bool(self.api_key),
        }
