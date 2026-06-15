import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from approck_fastapi_utils.idempotency import IdempotencyMiddleware, InMemoryIdempotencyStore


def _build_app(store: InMemoryIdempotencyStore) -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        IdempotencyMiddleware,
        store=store,
        ttl=300,
        validate_signature=True,
    )

    @app.post("/items")
    async def create_item(payload: dict) -> dict:
        return {"id": payload.get("id", "generated"), "payload": payload}

    return app


@pytest.mark.asyncio
async def test_same_idempotency_key_returns_cached_response() -> None:
    store = InMemoryIdempotencyStore()
    app = _build_app(store)
    headers = {"Idempotency-Key": "key-1"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response1 = await client.post("/items", json={"id": "item-1"}, headers=headers)
        response2 = await client.post("/items", json={"id": "item-1"}, headers=headers)

    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.json() == response2.json()
    assert response1.headers["X-Idempotency-Status"] == "new"
    assert response2.headers["X-Idempotency-Status"] == "hit"


@pytest.mark.asyncio
async def test_different_idempotency_keys_create_different_responses() -> None:
    store = InMemoryIdempotencyStore()
    app = _build_app(store)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response1 = await client.post(
            "/items",
            json={"id": "item-1"},
            headers={"Idempotency-Key": "key-1"},
        )
        response2 = await client.post(
            "/items",
            json={"id": "item-2"},
            headers={"Idempotency-Key": "key-2"},
        )

    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.json()["payload"]["id"] == "item-1"
    assert response2.json()["payload"]["id"] == "item-2"


@pytest.mark.asyncio
async def test_same_key_with_different_payload_returns_conflict() -> None:
    store = InMemoryIdempotencyStore()
    app = _build_app(store)
    headers = {"Idempotency-Key": "same-key"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response1 = await client.post("/items", json={"id": "item-1"}, headers=headers)
        response2 = await client.post("/items", json={"id": "item-2"}, headers=headers)

    assert response1.status_code == 200
    assert response2.status_code == 409
    assert "payload" in response2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_request_without_idempotency_key_is_not_cached() -> None:
    store = InMemoryIdempotencyStore()
    app = _build_app(store)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response1 = await client.post("/items", json={"id": "item-1"})
        response2 = await client.post("/items", json={"id": "item-1"})

    assert response1.status_code == 200
    assert response2.status_code == 200
    assert "X-Idempotency-Status" not in response1.headers
    assert "X-Idempotency-Status" not in response2.headers
