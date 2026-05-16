"""ConnectorRegistry — runtime registry for exchange connectors.

Similar to AdapterRegistry but for execution connectors.
"""

from typing import Optional, Type

from .base_connector import ExchangeConnector


class ConnectorRegistry:
    """Registry of exchange connector implementations."""

    _connectors: dict[str, Type[ExchangeConnector]] = {}

    @classmethod
    def register(cls, name: str, connector_class: Type[ExchangeConnector]) -> None:
        cls._connectors[name.lower()] = connector_class

    @classmethod
    def get(cls, name: str) -> Optional[Type[ExchangeConnector]]:
        return cls._connectors.get(name.lower())

    @classmethod
    def list_connectors(cls) -> list[str]:
        return list(cls._connectors.keys())

    @classmethod
    def create(cls, name: str) -> Optional[ExchangeConnector]:
        """Instantiate a connector by name."""
        connector_class = cls.get(name)
        if connector_class:
            return connector_class()
        return None


# Auto-register built-in connectors
def _register_builtin() -> None:
    try:
        from .binance_connector import BinanceConnector
        ConnectorRegistry.register("binance", BinanceConnector)
    except ImportError:
        pass

    try:
        from .bybit_connector import BybitConnector
        ConnectorRegistry.register("bybit", BybitConnector)
    except ImportError:
        pass

    try:
        from .okx_connector import OKXConnector
        ConnectorRegistry.register("okx", OKXConnector)
    except ImportError:
        pass

    try:
        from .hyperliquid_connector import HyperliquidConnector
        ConnectorRegistry.register("hyperliquid", HyperliquidConnector)
    except ImportError:
        pass

    try:
        from .aster_connector import AsterConnector
        ConnectorRegistry.register("aster", AsterConnector)
    except ImportError:
        pass


_register_builtin()
