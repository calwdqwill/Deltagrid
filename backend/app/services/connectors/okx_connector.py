"""OKX REST API connector.

Requires passphrase in addition to api_key and api_secret.
"""

import base64
import hmac
import hashlib
import json
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

BASE_URL = "https://www.okx.com"
TESTNET_URL = "https://www.okx.com"


class OKXConnector(ExchangeConnector):
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15.0)

    async def close(self) -> None:
        await self.client.aclose()

    @property
    def name(self) -> str:
        return "okx"

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

    def _base_url(self, credentials: DecryptedCredentials) -> str:
        return TESTNET_URL if credentials.is_testnet else BASE_URL

    def _timestamp(self) -> str:
        import datetime
        return datetime.datetime.utcnow().isoformat(timespec="milliseconds") + "Z"

    def _sign(self, timestamp: str, method: str, path: str, body: str, secret: str) -> str:
        message = timestamp + method.upper() + path + body
        mac = hmac.new(secret.encode(), message.encode(), hashlib.sha256)
        return base64.b64encode(mac.digest()).decode()

    def _headers(self, credentials: DecryptedCredentials, method: str, path: str, body: str = "") -> dict:
        ts = self._timestamp()
        signature = self._sign(ts, method, path, body, credentials.api_secret)
        return {
            "OK-ACCESS-KEY": credentials.api_key,
            "OK-ACCESS-SIGN": signature,
            "OK-ACCESS-TIMESTAMP": ts,
            "OK-ACCESS-PASSPHRASE": credentials.passphrase or "",
            "Content-Type": "application/json",
        }

    async def health_check(self, credentials: Optional[DecryptedCredentials] = None) -> bool:
        url = f"{BASE_URL}/api/v5/public/time"
        try:
            r = await self.client.get(url)
            return r.status_code == 200
        except Exception:
            return False

    async def get_ticker(self, symbol: str, credentials: DecryptedCredentials) -> Ticker:
        inst_id = symbol.replace("/", "-")
        url = f"{self._base_url(credentials)}/api/v5/market/ticker"
        r = await self.client.get(url, params={"instId": inst_id})
        r.raise_for_status()
        data = r.json()
        tick = data.get("data", [{}])[0]
        return Ticker(
            symbol=symbol,
            price=float(tick.get("last", 0)),
            bid=float(tick.get("bidPx", 0)) if tick.get("bidPx") else None,
            ask=float(tick.get("askPx", 0)) if tick.get("askPx") else None,
            volume_24h=float(tick.get("vol24h", 0)),
        )

    async def get_account_info(self, credentials: DecryptedCredentials) -> AccountInfo:
        path = "/api/v5/account/balance"
        headers = self._headers(credentials, "GET", path)
        url = f"{self._base_url(credentials)}{path}"
        r = await self.client.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()
        balances = {}
        for detail in data.get("data", [{}])[0].get("details", []):
            balances[detail["ccy"]] = {
                "free": float(detail.get("availBal", 0)),
                "locked": float(detail.get("frozenBal", 0)),
            }
        return AccountInfo(
            account_id="okx_main",
            balances=balances,
            permissions=["read", "trade"],
        )

    async def place_order(self, request: OrderRequest, credentials: DecryptedCredentials) -> OrderResult:
        path = "/api/v5/trade/order"
        body = json.dumps({
            "instId": request.symbol.replace("/", "-"),
            "tdMode": "cash",
            "side": request.side.lower(),
            "ordType": request.order_type.lower(),
            "sz": str(request.quantity),
            "px": str(request.price) if request.price else None,
            "clOrdId": request.client_order_id,
        }, separators=(",", ":"))
        headers = self._headers(credentials, "POST", path, body)
        url = f"{self._base_url(credentials)}{path}"
        r = await self.client.post(url, headers=headers, content=body)
        if r.status_code != 200:
            logger.error(f"OKX order error: {r.status_code} {r.text}")
            return OrderResult(
                exchange_order_id=None,
                status=OrderStatus.ERROR,
                filled_quantity=0,
                remaining_quantity=request.quantity,
                avg_fill_price=None,
                error_message=r.text,
            )
        data = r.json()
        result = data.get("data", [{}])[0]
        return OrderResult(
            exchange_order_id=result.get("ordId"),
            status=OrderStatus.PENDING,
            filled_quantity=0,
            remaining_quantity=request.quantity,
            avg_fill_price=None,
            raw_response=result,
        )

    async def cancel_order(self, order_id: str, credentials: DecryptedCredentials) -> bool:
        logger.warning("OKX cancel_order stub")
        return False

    async def get_order_status(self, order_id: str, symbol: str, credentials: DecryptedCredentials) -> OrderResult:
        path = "/api/v5/trade/order"
        params = {"instId": symbol.replace("/", "-"), "ordId": order_id}
        headers = self._headers(credentials, "GET", path)
        url = f"{self._base_url(credentials)}{path}"
        r = await self.client.get(url, headers=headers, params=params)
        r.raise_for_status()
        data = r.json()
        order = data.get("data", [{}])[0]
        return self._parse_order(order)

    def _parse_order(self, order: dict) -> OrderResult:
        status_map = {
            "live": OrderStatus.PENDING,
            "partially_filled": OrderStatus.PARTIALLY_FILLED,
            "filled": OrderStatus.FILLED,
            "canceled": OrderStatus.CANCELLED,
            "rejected": OrderStatus.REJECTED,
        }
        qty = float(order.get("sz", 0))
        filled = float(order.get("accFillSz", 0))
        return OrderResult(
            exchange_order_id=order.get("ordId"),
            status=status_map.get(order.get("state"), OrderStatus.ERROR),
            filled_quantity=filled,
            remaining_quantity=qty - filled,
            avg_fill_price=float(order.get("avgPx", 0)) if order.get("avgPx") else None,
            raw_response=order,
        )
