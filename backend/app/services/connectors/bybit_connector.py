"""Bybit V5 unified API connector.

Supports both Spot and Derivatives (Perp) via unified V5 endpoints.
"""

import hashlib
import hmac
import json
import time
import logging
from typing import Optional

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

BASE_URL = "https://api.bybit.com"
TESTNET_URL = "https://api-testnet.bybit.com"


class BybitConnector(ExchangeConnector):
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15.0)

    async def close(self) -> None:
        await self.client.aclose()

    @property
    def name(self) -> str:
        return "bybit"

    @property
    def capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(
            supports_spot=True,
            supports_perp=True,
            supports_margin=False,
            supports_market_order=True,
            supports_limit_order=True,
            supports_stop_loss=True,
            supports_cancel=True,
            supports_ws=True,
            rate_limit_requests_per_minute=1200,
        )

    def _base_url(self, credentials: DecryptedCredentials) -> str:
        return TESTNET_URL if credentials.is_testnet else BASE_URL

    def _sign(self, payload: str, secret: str) -> str:
        return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _headers(self, credentials: DecryptedCredentials, sign_payload: str = "") -> dict:
        ts = str(self._timestamp())
        recv_window = "5000"
        signature = self._sign(ts + credentials.api_key + recv_window + sign_payload, credentials.api_secret)
        return {
            "X-BAPI-API-KEY": credentials.api_key,
            "X-BAPI-TIMESTAMP": ts,
            "X-BAPI-SIGN": signature,
            "X-BAPI-RECV-WINDOW": recv_window,
            "Content-Type": "application/json",
        }

    async def health_check(self, credentials: Optional[DecryptedCredentials] = None) -> bool:
        url = f"{BASE_URL}/v5/market/time"
        try:
            r = await self.client.get(url)
            return r.status_code == 200
        except Exception:
            return False

    async def get_ticker(self, symbol: str, credentials: DecryptedCredentials) -> Ticker:
        url = f"{self._base_url(credentials)}/v5/market/tickers"
        params = {"category": "spot", "symbol": symbol.replace("/", "")}
        r = await self.client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        tick = data.get("result", {}).get("list", [{}])[0]
        return Ticker(
            symbol=symbol,
            price=float(tick.get("lastPrice", 0)),
            bid=float(tick.get("bid1Price", 0)) if tick.get("bid1Price") else None,
            ask=float(tick.get("ask1Price", 0)) if tick.get("ask1Price") else None,
            volume_24h=float(tick.get("volume24h", 0)),
        )

    async def get_account_info(self, credentials: DecryptedCredentials) -> AccountInfo:
        url = f"{self._base_url(credentials)}/v5/account/wallet-balance"
        headers = self._headers(credentials)
        r = await self.client.get(url, headers=headers, params={"accountType": "UNIFIED"})
        r.raise_for_status()
        data = r.json()
        balances = {}
        for coin in data.get("result", {}).get("list", [{}])[0].get("coin", []):
            balances[coin["coin"]] = {
                "free": float(coin.get("walletBalance", 0)),
                "locked": float(coin.get("locked", 0)),
            }
        return AccountInfo(
            account_id="bybit_unified",
            balances=balances,
            permissions=["SpotTrade", "DerivativesTrade"],
        )

    async def place_order(self, request: OrderRequest, credentials: DecryptedCredentials) -> OrderResult:
        body = {
            "category": "spot",
            "symbol": request.symbol.replace("/", ""),
            "side": request.side.capitalize(),
            "orderType": request.order_type.upper(),
            "qty": str(request.quantity),
        }
        if request.order_type == "limit" and request.price:
            body["price"] = str(request.price)
        if request.client_order_id:
            body["orderLinkId"] = request.client_order_id

        payload = json.dumps(body, separators=(",", ":"))
        url = f"{self._base_url(credentials)}/v5/order/create"
        headers = self._headers(credentials, payload)
        r = await self.client.post(url, headers=headers, content=payload)
        if r.status_code != 200:
            logger.error(f"Bybit order error: {r.status_code} {r.text}")
            return OrderResult(
                exchange_order_id=None,
                status=OrderStatus.ERROR,
                filled_quantity=0,
                remaining_quantity=request.quantity,
                avg_fill_price=None,
                error_message=r.text,
            )
        data = r.json()
        result = data.get("result", {})
        return OrderResult(
            exchange_order_id=result.get("orderId"),
            status=OrderStatus.PENDING,
            filled_quantity=0,
            remaining_quantity=request.quantity,
            avg_fill_price=None,
            raw_response=result,
        )

    async def cancel_order(self, order_id: str, credentials: DecryptedCredentials) -> bool:
        logger.warning("Bybit cancel_order stub: requires symbol/category params")
        return False

    async def get_order_status(self, order_id: str, symbol: str, credentials: DecryptedCredentials) -> OrderResult:
        url = f"{self._base_url(credentials)}/v5/order/realtime"
        params = {"category": "spot", "symbol": symbol.replace("/", ""), "orderId": order_id}
        headers = self._headers(credentials)
        r = await self.client.get(url, headers=headers, params=params)
        r.raise_for_status()
        data = r.json()
        order = data.get("result", {}).get("list", [{}])[0]
        return self._parse_order(order)

    def _parse_order(self, order: dict) -> OrderResult:
        status_map = {
            "Created": OrderStatus.PENDING,
            "New": OrderStatus.PENDING,
            "Rejected": OrderStatus.REJECTED,
            "PartiallyFilled": OrderStatus.PARTIALLY_FILLED,
            "PartiallyFilledCanceled": OrderStatus.PARTIALLY_FILLED,
            "Filled": OrderStatus.FILLED,
            "Cancelled": OrderStatus.CANCELLED,
        }
        qty = float(order.get("qty", 0))
        filled = float(order.get("cumExecQty", 0))
        return OrderResult(
            exchange_order_id=order.get("orderId"),
            status=status_map.get(order.get("orderStatus"), OrderStatus.ERROR),
            filled_quantity=filled,
            remaining_quantity=qty - filled,
            avg_fill_price=float(order.get("avgPrice", 0)) if order.get("avgPrice") else None,
            raw_response=order,
        )
