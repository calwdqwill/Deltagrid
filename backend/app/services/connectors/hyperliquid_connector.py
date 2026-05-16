"""Hyperliquid direct REST API connector.

Uses Hyperliquid's public + private REST endpoints.
No api_secret needed for read-only; wallet private key needed for trading.
For Phase 3 foundation we implement read + placeholder write.
"""

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

BASE_URL = "https://api.hyperliquid.xyz"


class HyperliquidConnector(ExchangeConnector):
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15.0)

    async def close(self) -> None:
        await self.client.aclose()

    @property
    def name(self) -> str:
        return "hyperliquid"

    @property
    def capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(
            supports_spot=False,
            supports_perp=True,
            supports_margin=False,
            supports_market_order=True,
            supports_limit_order=True,
            supports_stop_loss=True,
            supports_cancel=True,
            supports_ws=True,
            rate_limit_requests_per_minute=6000,
        )

    async def health_check(self, credentials: Optional[DecryptedCredentials] = None) -> bool:
        try:
            r = await self.client.post(f"{BASE_URL}/info", json={"type": "meta"})
            return r.status_code == 200
        except Exception:
            return False

    async def get_ticker(self, symbol: str, credentials: DecryptedCredentials) -> Ticker:
        """Fetch latest price from Hyperliquid allMids endpoint."""
        r = await self.client.post(f"{BASE_URL}/info", json={"type": "allMids"})
        r.raise_for_status()
        data = r.json()
        coin = symbol.replace("/USDT", "").replace("/USD", "").upper()
        price = float(data.get(coin, 0))
        return Ticker(
            symbol=symbol,
            price=price,
        )

    async def get_account_info(self, credentials: DecryptedCredentials) -> AccountInfo:
        """Fetch clearinghouse state for the wallet address (api_key used as address)."""
        address = credentials.api_key
        r = await self.client.post(
            f"{BASE_URL}/info",
            json={"type": "clearinghouseState", "user": address},
        )
        r.raise_for_status()
        data = r.json()
        balances = {}
        for asset in data.get("assetPositions", []):
            pos = asset.get("position", {})
            coin = pos.get("coin", "UNKNOWN")
            balances[coin] = {
                "free": float(pos.get("szi", 0)),
                "locked": 0.0,
            }
        return AccountInfo(
            account_id=address,
            balances=balances,
            permissions=["perp_trade"],
        )

    async def place_order(self, request: OrderRequest, credentials: DecryptedCredentials) -> OrderResult:
        """Hyperliquid trading requires wallet signatures (EIP-712).
        For Phase 3 foundation we return a placeholder indicating
        that direct trading needs wallet integration.
        """
        logger.warning("Hyperliquid direct trading requires wallet signing; returning placeholder")
        return OrderResult(
            exchange_order_id=None,
            status=OrderStatus.ERROR,
            filled_quantity=0,
            remaining_quantity=request.quantity,
            avg_fill_price=None,
            error_message="Hyperliquid direct trading requires wallet integration (Phase 3+).",
        )

    async def cancel_order(self, order_id: str, credentials: DecryptedCredentials) -> bool:
        logger.warning("Hyperliquid cancel_order: wallet signing required")
        return False

    async def get_order_status(self, order_id: str, symbol: str, credentials: DecryptedCredentials) -> OrderResult:
        logger.warning("Hyperliquid get_order_status: stub implementation")
        return OrderResult(
            exchange_order_id=order_id,
            status=OrderStatus.PENDING,
            filled_quantity=0,
            remaining_quantity=0,
            avg_fill_price=None,
        )
