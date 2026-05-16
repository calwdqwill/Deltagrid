import json
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Optional, Any


class CacheService(ABC):
    """Abstract cache service interface.

    Phase 1: In-memory dict implementation.
    Phase 2+: Redis implementation via same interface.
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        ...

    @abstractmethod
    async def clear(self) -> None:
        ...

    @abstractmethod
    async def info(self) -> dict:
        ...


class InMemoryCacheService(CacheService):
    """LRU in-memory cache with TTL expiry.

    Phase 4: Upgraded from FIFO to LRU using OrderedDict.
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 60):
        self._store: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl

    async def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expiry = entry
        if time.time() > expiry:
            self._store.pop(key, None)
            return None
        # Move to end (most recently used)
        self._store.move_to_end(key)
        return value

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        if len(self._store) >= self._max_size and key not in self._store:
            # Pop oldest (least recently used)
            self._store.popitem(last=False)
        expiry = time.time() + ttl_seconds
        self._store[key] = (value, expiry)
        # Move to end (most recently used)
        self._store.move_to_end(key)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def clear(self) -> None:
        self._store.clear()

    async def info(self) -> dict:
        now = time.time()
        valid = sum(1 for _, expiry in self._store.values() if expiry > now)
        return {
            "backend": "in_memory",
            "total_keys": len(self._store),
            "valid_keys": valid,
            "max_size": self._max_size,
            "default_ttl": self._default_ttl,
        }


class RedisCacheService(CacheService):
    """Redis-backed cache implementation.

    Uses the same CacheService ABC so it can be swapped via config.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0", default_ttl: int = 60):
        import redis.asyncio as redis
        self._client = redis.from_url(redis_url, decode_responses=True)
        self._default_ttl = default_ttl

    async def get(self, key: str) -> Optional[Any]:
        raw = await self._client.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        payload = json.dumps(value, default=str)
        await self._client.setex(key, ttl_seconds, payload)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def clear(self) -> None:
        await self._client.flushdb()

    async def info(self) -> dict:
        try:
            info = await self._client.info()
            return {
                "backend": "redis",
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "default_ttl": self._default_ttl,
            }
        except Exception as e:
            return {"backend": "redis", "error": str(e)}
