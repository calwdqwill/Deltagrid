from typing import Optional

from app.adapters.base import BaseAdapter
from app.adapters.coingecko_adapter import CoinGeckoAdapter
from app.adapters.hyperliquid_adapter import HyperliquidAdapter
from app.adapters.aster_adapter import AsterAdapter
from app.adapters.lighter_adapter import LighterAdapter


class AdapterRegistry:
    """Factory/registry for data source adapters.

    Allows runtime adapter registration and lookup.
    Phase 3: direct exchange APIs register here alongside CG.
    """

    def __init__(self):
        self._adapters: dict[str, BaseAdapter] = {}

    def register(self, name: str, adapter: BaseAdapter) -> None:
        self._adapters[name] = adapter

    def get(self, name: str) -> Optional[BaseAdapter]:
        return self._adapters.get(name)

    def list_adapters(self) -> list[str]:
        return list(self._adapters.keys())

    async def health_check_all(self) -> dict[str, dict]:
        results = {}
        for name, adapter in self._adapters.items():
            try:
                results[name] = await adapter.health_check()
            except Exception as e:
                results[name] = {"status": "error", "error": str(e)}
        return results


def create_default_registry(cg_api_key: Optional[str] = None) -> AdapterRegistry:
    registry = AdapterRegistry()
    registry.register("coingecko", CoinGeckoAdapter(api_key=cg_api_key))
    registry.register("hyperliquid", HyperliquidAdapter(cg_api_key=cg_api_key))
    registry.register("aster", AsterAdapter(cg_api_key=cg_api_key))
    registry.register("lighter", LighterAdapter(cg_api_key=cg_api_key))
    return registry
