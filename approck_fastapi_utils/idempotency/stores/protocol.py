from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class IdempotencyStore(Protocol):
    """Minimal async key-value store used by ``IdempotencyMiddleware``."""

    async def get(self, key: str) -> str | None: ...

    async def set(self, key: str, value: str, *, ex: int | None = None, nx: bool = False) -> bool: ...

    async def setex(self, key: str, time: int, value: str) -> Any: ...

    async def delete(self, key: str) -> Any: ...
