from typing import Literal

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

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

ExceptionProfile = Literal["api", "internal", "minimal"]

_UNPROCESSABLE_ENTITY = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)

_STATUS_CODE_BY_TYPE: dict[type[CustomException], int] = {
    Unauthorized: status.HTTP_401_UNAUTHORIZED,
    Forbidden: status.HTTP_403_FORBIDDEN,
    NotFound: status.HTTP_404_NOT_FOUND,
    Conflict: status.HTTP_409_CONFLICT,
    UnprocessableEntity: _UNPROCESSABLE_ENTITY,
    BadGateway: status.HTTP_502_BAD_GATEWAY,
    ServiceUnavailable: status.HTTP_503_SERVICE_UNAVAILABLE,
}


def resolve_custom_exception_status_code(exc: CustomException) -> int:
    """Resolve HTTP status code for a custom exception."""
    if exc.status_code is not None:
        return exc.status_code

    for base_exc, base_status_code in _STATUS_CODE_BY_TYPE.items():
        if isinstance(exc, base_exc):
            return base_status_code

    return status.HTTP_400_BAD_REQUEST


def custom_exception_response(exc: CustomException) -> JSONResponse:
    """Build a JSON response for a custom exception."""
    return JSONResponse(
        content={"successful": False, "code": exc.__class__.__name__, "detail": str(exc)},
        status_code=resolve_custom_exception_status_code(exc),
    )


async def http_exception_handler(
    _: Request,
    exc: HTTPException,
) -> JSONResponse:
    response = JSONResponse(
        content={"successful": False, "detail": exc.detail},
        status_code=exc.status_code,
    )
    if exc.headers is not None:
        response.init_headers(exc.headers)

    return response


async def custom_exception_handler(
    _: Request,
    exc: CustomException,
) -> JSONResponse:
    return custom_exception_response(exc)


async def validation_exception_handler(
    _: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        content={
            "successful": False,
            "code": "ValidationError",
            "detail": exc.errors(),
        },
        status_code=_UNPROCESSABLE_ENTITY,
    )


def register_exception_handlers(
    app: FastAPI,
    *,
    profile: ExceptionProfile = "api",
    database_sanitize: bool = False,
) -> None:
    """Register common exception handlers with a predictable preset."""
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]

    if profile == "minimal":
        app.add_exception_handler(CustomException, custom_exception_handler)  # type: ignore[arg-type]
        return

    app.add_exception_handler(CustomException, custom_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]

    try:
        from sqlalchemy.exc import DBAPIError, NoResultFound

        from .sqlalchemy.exception_handlers import create_database_error_handler, database_not_found_handler
    except ImportError:
        return

    app.add_exception_handler(NoResultFound, database_not_found_handler)  # type: ignore[arg-type]

    if profile == "internal":
        app.add_exception_handler(
            DBAPIError,
            create_database_error_handler(sanitize=database_sanitize),
        )  # type: ignore[arg-type]
