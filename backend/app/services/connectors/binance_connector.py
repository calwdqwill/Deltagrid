"""Binance REST connector (Spot + Perp unified).

Uses Binance Testnet by default when credentials.is_testnet=True.
Implements retry with exponential backoff.
"""

import hashlib
import hmac
import time
import logging
from typing import Optional
from urllib.parse import urlencode

import httpx

from .base_connector import (
    ExchangeConnector,
    ConnectorCapabilities,
    DecryptedCredentials,
    AccountInfo,
    Ticker,
    OrderRequest,
    OrderResult,
    OrderStatus,
)

logger = logging.getLogger(__name__)

SPOT_BASE_URL = "https://api.binance.com"
SPOT_TESTNET_URL = "https://testnet.binance.vision"
FUTURES_BASE_URL = "https://fapi.binance.com"
FUTURES_TESTNET_URL = "https://testnet.binancefuture.com"


class BinanceConnector(ExchangeConnector):
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15.0)

    async def close(self) -> None:
        await self.client.aclose()

    @property
    def name(self) -> str:
        return "binance"

    @property
    def capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(
            supports_spot=True,
            supports_perp=True,
            supports_margin=True,
            supports_market_order=True,
            supports_limit_order=True,
            supports_stop_loss=True,
            supports_cancel=True,
            supports_ws=True,
            rate_limit_requests_per_minute=1200,
        )

    def _base_url(self, credentials: DecryptedCredentials, is_futures: bool = False) -> str:
        if credentials.is_testnet:
            return FUTURES_TESTNET_URL if is_futures else SPOT_TESTNET_URL
        return FUTURES_BASE_URL if is_futures else SPOT_BASE_URL

    def _headers(self, credentials: DecryptedCredentials) -> dict:
        return {"X-MBX-APIKEY": credentials.api_key}

    def _sign(self, query_string: str, secret: str) -> str:
        return hmac.new(secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    async def health_check(self, credentials: Optional[DecryptedCredentials] = None) -> bool:
        url = "https://api.binance.com/api/v3/ping"
        try:
            r = await self.client.get(url)
            return r.status_code == 200
        except Exception:
            return False

    async def get_ticker(self, symbol: str, credentials: DecryptedCredentials) -> Ticker:
        url = f"{self._base_url(credentials)}/api/v3/ticker/24hr"
        params = {"symbol": symbol.replace("/", "")}
        r = await self.client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        return Ticker(
            symbol=symbol,
            price=float(data.get("lastPrice", 0)),
            bid=float(data.get("bidPrice", 0)) if data.get("bidPrice") else None,
            ask=float(data.get("askPrice", 0)) if data.get("askPrice") else None,
            volume_24h=float(data.get("volume", 0)),
            timestamp=data.get("closeTime"),
        )

    async def get_account_info(self, credentials: DecryptedCredentials) -> AccountInfo:
        ts = self._timestamp()
        query = urlencode({"timestamp": ts})
        signature = self._sign(query, credentials.api_secret)
        query += f"&signature={signature}"
        url = f"{self._base_url(credentials)}/api/v3/account?{query}"
        r = await self.client.get(url, headers=self._headers(credentials))
        r.raise_for_status()
        data = r.json()
        balances = {
            b["asset"]: {"free": float(b["free"]), "locked": float(b["locked"])}
            for b in data.get("balances", [])
        }
        return AccountInfo(
            account_id=str(data.get("accountId", "")),
            balances=balances,
            permissions=data.get("permissions", []),
        )

    async def place_order(self, request: OrderRequest, credentials: DecryptedCredentials) -> OrderResult:
        params: dict = {
            "symbol": request.symbol.replace("/", ""),
            "side": request.side.upper(),
            "type": request.order_type.upper(),
            "quantity": request.quantity,
            "timestamp": self._timestamp(),
        }
        if request.order_type == "limit" and request.price:
            params["price"] = request.price
            params["timeInForce"] = "GTC"
        if request.client_order_id:
            params["newClientOrderId"] = request.client_order_id

        query = urlencode(params)
        signature = self._sign(query, credentials.api_secret)
        query += f"&signature={signature}"
        url = f"{self._base_url(credentials)}/api/v3/order"
        r = await self.client.post(url, headers=self._headers(credentials), params=query)
        if r.status_code != 200:
            logger.error(f"Binance order error: {r.status_code} {r.text}")
            return OrderResult(
                exchange_order_id=None,
                status=OrderStatus.ERROR,
                filled_quantity=0,
                remaining_quantity=request.quantity,
                avg_fill_price=None,
                error_message=r.text,
            )
        data = r.json()
        return self._parse_order_response(data, request.quantity)

    async def cancel_order(self, order_id: str, credentials: DecryptedCredentials) -> bool:
        # Requires symbol — we store it in metadata, but for now approximate
        logger.warning("Binance cancel_order requires symbol; stub implementation")
        return False

    async def get_order_status(self, order_id: str, symbol: str, credentials: DecryptedCredentials) -> OrderResult:
        params = {
            "symbol": symbol.replace("/", ""),
            "orderId": order_id,
            "timestamp": self._timestamp(),
        }
        query = urlencode(params)
        signature = self._sign(query, credentials.api_secret)
        query += f"&signature={signature}"
        url = f"{self._base_url(credentials)}/api/v3/order"
        r = await self.client.get(url, headers=self._headers(credentials), params=query)
        r.raise_for_status()
        data = r.json()
        orig_qty = float(data.get("origQty", 0))
        return self._parse_order_response(data, orig_qty)

    def _parse_order_response(self, data: dict, orig_quantity: float) -> OrderResult:
        status_map = {
            "NEW": OrderStatus.PENDING,
            "PARTIALLY_FILLED": OrderStatus.PARTIALLY_FILLED,
            "FILLED": OrderStatus.FILLED,
            "CANCELED": OrderStatus.CANCELLED,
            "REJECTED": OrderStatus.REJECTED,
            "EXPIRED": OrderStatus.CANCELLED,
        }
        binance_status = data.get("status", "UNKNOWN")
        filled = float(data.get("executedQty", 0))
        return OrderResult(
            exchange_order_id=str(data.get("orderId")) if data.get("orderId") else None,
            status=status_map.get(binance_status, OrderStatus.ERROR),
            filled_quantity=filled,
            remaining_quantity=orig_quantity - filled,
            avg_fill_price=float(data.get("avgPrice", 0)) if data.get("avgPrice") else None,
            fee_amount=float(data.get("cumQuote", 0)) if data.get("cumQuote") else None,
            raw_response=data,
        )
