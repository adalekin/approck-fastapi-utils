"""FastAPI utilities for Approck services."""

from .auth import JwtPayload, ensure_current_superuser, ensure_current_user, optional_current_user
from .exception_handlers import (
    custom_exception_handler,
    http_exception_handler,
    register_exception_handlers,
    resolve_custom_exception_status_code,
    validation_exception_handler,
)
from .exceptions import (
    BadGateway,
    Conflict,
    CustomException,
    Forbidden,
    NotFound,
    ServiceUnavailable,
    Unauthorized,
    UnprocessableEntity,
)
from .gateway import build_gateway_headers
from .idempotency import IdempotencyMiddleware, IdempotencyStore, InMemoryIdempotencyStore
from .jwt import decode_payload, encode_payload, get_token_from_header
from .response import HTTP_404_NOT_FOUND
from .responses import (
    FailedResponse,
    SuccessfulResponse,
    custom_exception_response_schema,
    error_response_schema,
)
from .types import CommaSeparatedList

__all__ = [
    "BadGateway",
    "CommaSeparatedList",
    "Conflict",
    "CustomException",
    "FailedResponse",
    "Forbidden",
    "HTTP_404_NOT_FOUND",
    "IdempotencyMiddleware",
    "IdempotencyStore",
    "InMemoryIdempotencyStore",
    "JwtPayload",
    "NotFound",
    "ServiceUnavailable",
    "SuccessfulResponse",
    "Unauthorized",
    "UnprocessableEntity",
    "build_gateway_headers",
    "custom_exception_handler",
    "custom_exception_response_schema",
    "decode_payload",
    "encode_payload",
    "ensure_current_superuser",
    "ensure_current_user",
    "error_response_schema",
    "get_token_from_header",
    "http_exception_handler",
    "optional_current_user",
    "register_exception_handlers",
    "resolve_custom_exception_status_code",
    "validation_exception_handler",
]
