from typing import Any

from fastapi import FastAPI

from . import jwt
from .auth import ensure_current_user


def make_jwt_payload_header(*, user_id: int = 1, is_superuser: bool = False, **extra: Any) -> str:
    """Encode a JWT payload header value for tests."""
    payload = {"user_id": user_id, "is_superuser": is_superuser, **extra}
    return jwt.encode_payload(payload)


def auth_headers(
    jwt_payload: str | None = None,
    *,
    access_token: str | None = None,
    user_id: int = 1,
    **claims: Any,
) -> dict[str, str]:
    """Build request headers with ``X-JWT-Payload`` and optional ``Authorization``."""
    headers = {"X-JWT-Payload": jwt_payload or make_jwt_payload_header(user_id=user_id, **claims)}

    if access_token is not None:
        headers["Authorization"] = f"Bearer {access_token}"

    return headers


def override_current_user(app: FastAPI, user_id: int = 1, **claims: Any) -> dict:
    """Override ``ensure_current_user`` in tests and return the injected payload."""
    payload = {"user_id": user_id, **claims}

    async def _test_user() -> dict:
        return payload

    app.dependency_overrides[ensure_current_user] = _test_user
    return payload
