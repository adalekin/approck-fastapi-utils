from __future__ import annotations

from typing import Any


class RedisIdempotencyStore:
    """Redis-backed idempotency store.

    Wrap an existing ``redis.asyncio.Redis`` client configured with
    ``decode_responses=True``.
    """

    def __init__(self, client: Any) -> None:
        self._client = client

    async def get(self, key: str) -> str | None:
        value = await self._client.get(key)
        return value if value is None or isinstance(value, str) else str(value)

    async def set(self, key: str, value: str, *, ex: int | None = None, nx: bool = False) -> bool:
        result = await self._client.set(key, value, ex=ex, nx=nx)
        return bool(result)

    async def setex(self, key: str, time: int, value: str) -> Any:
        return await self._client.setex(key, time, value)

    async def delete(self, key: str) -> Any:
        return await self._client.delete(key)

    async def aclose(self) -> None:
        await self._client.aclose()
