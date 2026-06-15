class InMemoryIdempotencyStore:
    """In-memory store for tests and local development."""

    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self._data.get(key)

    async def set(self, key: str, value: str, *, ex: int | None = None, nx: bool = False) -> bool:
        if nx and key in self._data:
            return False
        self._data[key] = value
        return True

    async def setex(self, key: str, time: int, value: str) -> None:
        self._data[key] = value

    async def delete(self, key: str) -> None:
        self._data.pop(key, None)

    async def aclose(self) -> None:
        self._data.clear()
