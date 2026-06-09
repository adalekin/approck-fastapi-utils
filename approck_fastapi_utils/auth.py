from typing import Literal, TypedDict

from fastapi import Depends, Header

from . import jwt
from .exceptions import Forbidden, Unauthorized


class JwtPayload(TypedDict, total=False):
    user_id: int
    is_superuser: bool
    sub: str


def ensure_current_user(
    x_jwt_payload: str = Header(..., alias="X-JWT-Payload"),
) -> dict:
    """Return decoded JWT payload or raise ``Unauthorized`` when the header is invalid."""
    payload = jwt.decode_payload(x_jwt_payload)

    if not payload:
        raise Unauthorized("Invalid token")

    return payload


def optional_current_user(*, on_invalid: Literal["none", "forbidden"] = "none"):
    """Factory for an optional auth dependency.

    ``on_invalid="none"`` returns ``None`` for missing or invalid payloads.
    ``on_invalid="forbidden"`` raises ``Forbidden`` for invalid payloads.
    """

    def _optional_current_user(
        x_jwt_payload: str | None = Header(None, alias="X-JWT-Payload"),
    ) -> dict | None:
        if not x_jwt_payload:
            return None

        payload = jwt.decode_payload(x_jwt_payload)
        if not payload:
            if on_invalid == "forbidden":
                raise Forbidden("Access denied")
            return None

        return payload

    return _optional_current_user


def ensure_current_superuser(
    payload: dict = Depends(ensure_current_user),
) -> dict:
    """Require ``is_superuser`` in the decoded JWT payload."""
    if not payload.get("is_superuser"):
        raise Forbidden("Superuser access required")

    return payload
