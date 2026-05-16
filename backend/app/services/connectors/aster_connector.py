"""Aster connector stub — placeholder for Increment E."""

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


class AsterConnector(ExchangeConnector):
    @property
    def name(self) -> str:
        return "aster"

    @property
    def capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(
            supports_spot=False,
            supports_perp=True,
            supports_margin=False,
            supports_market_order=True,
            supports_limit_order=True,
            supports_stop_loss=False,
            supports_cancel=True,
            supports_ws=False,
            rate_limit_requests_per_minute=600,
        )

    async def health_check(self, credentials=None):
        return True

    async def get_account_info(self, credentials):
        raise NotImplementedError("Aster connector: Increment E")

    async def get_ticker(self, symbol, credentials):
        raise NotImplementedError("Aster connector: Increment E")

    async def place_order(self, request, credentials):
        raise NotImplementedError("Aster connector: Increment E")

    async def cancel_order(self, order_id, credentials):
        raise NotImplementedError("Aster connector: Increment E")

    async def get_order_status(self, order_id, symbol, credentials):
        raise NotImplementedError("Aster connector: Increment E")

    async def close(self) -> None:
        pass
