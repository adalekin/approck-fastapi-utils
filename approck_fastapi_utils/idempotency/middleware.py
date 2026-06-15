from __future__ import annotations

import asyncio
import hashlib
import json
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .stores.protocol import IdempotencyStore


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Handle ``Idempotency-Key`` for mutating HTTP requests.

    The middleware:
    - Applies to POST/PUT/PATCH/DELETE when ``Idempotency-Key`` is present
    - Caches successful responses (< 400) in the configured store
    - Returns cached responses for duplicate requests with the same key
    - Validates request signatures to prevent key reuse with different payloads
    """

    MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

    def __init__(
        self,
        app,
        store: IdempotencyStore,
        *,
        ttl: int = 300,
        key_header: str = "Idempotency-Key",
        status_header: str = "X-Idempotency-Status",
        signature_header: str = "X-Idempotency-Signature",
        validate_signature: bool = True,
    ) -> None:
        super().__init__(app)
        self.store = store
        self.ttl = ttl
        self.key_header = key_header
        self.status_header = status_header
        self.signature_header = signature_header
        self.validate_signature = validate_signature

    async def dispatch(self, request: Request, call_next):
        if request.method not in self.MUTATING_METHODS:
            return await call_next(request)

        idempotency_key = request.headers.get(self.key_header)
        if not idempotency_key:
            return await call_next(request)

        body = await request.body()
        request_signature = self._compute_signature(body, request) if self.validate_signature else None

        cache_key = f"idempotency:{idempotency_key}"
        lock_key = f"idempotency:lock:{idempotency_key}"

        lock_acquired = await self.store.set(lock_key, "1", ex=30, nx=True)

        if not lock_acquired:
            cached_response = await self._wait_for_cached_response(
                cache_key,
                idempotency_key,
                request_signature,
            )
            if cached_response is not None:
                return cached_response

            return self._conflict_response("Request is being processed, please retry later")

        try:
            cached_response = await self._build_cached_response(
                cache_key,
                idempotency_key,
                request_signature,
            )
            if cached_response is not None:
                return cached_response

            async def receive():
                return {"type": "http.request", "body": body}

            original_receive = request._receive
            request._receive = receive

            try:
                response = await call_next(request)
            finally:
                request._receive = original_receive

            if response.status_code < 400:
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk

                await self.store.setex(
                    cache_key,
                    self.ttl,
                    json.dumps(
                        {
                            "body": response_body.decode() if isinstance(response_body, bytes) else str(response_body),
                            "status_code": response.status_code,
                            "headers": dict(response.headers),
                            "media_type": response.media_type or "application/json",
                            "signature": request_signature,
                        }
                    ),
                )

                response_headers = dict(response.headers)
                response_headers[self.key_header] = idempotency_key
                response_headers[self.status_header] = "new"
                if self.validate_signature and request_signature:
                    response_headers[self.signature_header] = request_signature

                return Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=response_headers,
                    media_type=response.media_type,
                )

            return response
        finally:
            await self.store.delete(lock_key)

    async def _wait_for_cached_response(
        self,
        cache_key: str,
        idempotency_key: str,
        request_signature: str | None,
    ) -> Response | None:
        for _ in range(30):
            await asyncio.sleep(1)
            cached = await self.store.get(cache_key)
            if cached:
                return self._response_from_cache(
                    json.loads(cached),
                    idempotency_key,
                    request_signature,
                )
        return None

    async def _build_cached_response(
        self,
        cache_key: str,
        idempotency_key: str,
        request_signature: str | None,
    ) -> Response | None:
        cached = await self.store.get(cache_key)
        if not cached:
            return None

        return self._response_from_cache(
            json.loads(cached),
            idempotency_key,
            request_signature,
        )

    def _response_from_cache(
        self,
        cached_data: dict[str, Any],
        idempotency_key: str,
        request_signature: str | None,
    ) -> Response:
        if self.validate_signature and request_signature:
            if cached_data.get("signature") != request_signature:
                return self._conflict_response("Request payload does not match previous Idempotency-Key usage")

        response_headers = dict(cached_data["headers"])
        response_headers[self.key_header] = idempotency_key
        response_headers[self.status_header] = "hit"
        if self.validate_signature and request_signature:
            response_headers[self.signature_header] = request_signature

        return Response(
            content=cached_data["body"],
            status_code=cached_data["status_code"],
            headers=response_headers,
            media_type=cached_data.get("media_type", "application/json"),
        )

    def _compute_signature(self, body: bytes, request: Request) -> str:
        """Compute request signature for validation."""
        query_string = str(request.url.query)
        body_text = body.decode() if isinstance(body, bytes) else body
        signature_data = f"{request.method}:{request.url.path}:{query_string}:{body_text}"
        return hashlib.sha256(signature_data.encode()).hexdigest()

    def _conflict_response(self, detail: str) -> Response:
        return Response(
            content=json.dumps({"detail": detail}),
            status_code=409,
            media_type="application/json",
        )
