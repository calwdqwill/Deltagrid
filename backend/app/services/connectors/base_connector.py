"""ExchangeConnector ABC — unified interface for all CEX and Perp DEX connectors.

This module defines the contract that every exchange connector must implement.
No exchange-specific logic leaks outside the connector layer.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class OrderStatus(str, Enum):
    PENDING = "pending"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    ERROR = "error"


@dataclass
class ConnectorCapabilities:
    supports_spot: bool = False
    supports_perp: bool = False
    supports_margin: bool = False
    supports_market_order: bool = False
    supports_limit_order: bool = False
    supports_stop_loss: bool = False
    supports_cancel: bool = False
    supports_ws: bool = False
    rate_limit_requests_per_minute: int = 1200


@dataclass
class DecryptedCredentials:
    api_key: str
    api_secret: str
    passphrase: Optional[str] = None
    is_testnet: bool = False


@dataclass
class AccountInfo:
    account_id: str
    balances: dict  # {asset: {"free": float, "locked": float}}
    permissions: list[str]


@dataclass
class Ticker:
    symbol: str
    price: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume_24h: Optional[float] = None
    timestamp: Optional[int] = None


@dataclass
class OrderRequest:
    symbol: str
    side: str  # "buy" | "sell"
    order_type: str  # "market" | "limit" | "stop_loss" | "take_profit"
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    client_order_id: Optional[str] = None


@dataclass
class OrderResult:
    exchange_order_id: Optional[str]
    status: OrderStatus
    filled_quantity: float
    remaining_quantity: float
    avg_fill_price: Optional[float]
    fee_amount: Optional[float] = None
    fee_currency: Optional[str] = None
    raw_response: Optional[dict] = None
    error_message: Optional[str] = None


class ExchangeConnector(ABC):
    """Abstract base for all exchange connectors."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Exchange identifier, e.g. 'binance', 'bybit', 'hyperliquid'."""
        ...

    @property
    @abstractmethod
    def capabilities(self) -> ConnectorCapabilities:
        ...

    @abstractmethod
    async def get_account_info(self, credentials: DecryptedCredentials) -> AccountInfo:
        """Fetch account balances and permissions."""
        ...

    @abstractmethod
    async def get_ticker(self, symbol: str, credentials: DecryptedCredentials) -> Ticker:
        """Fetch latest ticker for a symbol."""
        ...

    @abstractmethod
    async def place_order(self, request: OrderRequest, credentials: DecryptedCredentials) -> OrderResult:
        """Submit an order to the exchange."""
        ...

    @abstractmethod
    async def cancel_order(self, order_id: str, credentials: DecryptedCredentials) -> bool:
        """Cancel an open order. Returns True if cancelled successfully."""
        ...

    @abstractmethod
    async def get_order_status(self, order_id: str, symbol: str, credentials: DecryptedCredentials) -> OrderResult:
        """Query current status of an order."""
        ...

    @abstractmethod
    async def health_check(self, credentials: Optional[DecryptedCredentials] = None) -> bool:
        """Quick connectivity check. Returns True if exchange API is reachable."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close any underlying HTTP clients or connections."""
        ...
