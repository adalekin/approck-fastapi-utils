import logging
from collections.abc import Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, IntegrityError, NoResultFound

from ..exception_handlers import custom_exception_response
from ..exceptions import Conflict

logger = logging.getLogger(__name__)


def _extract_database_detail(exc: DBAPIError) -> str:
    if exc.orig is not None:
        return str(exc.orig)
    return str(exc)


def create_database_error_handler(*, sanitize: bool = False) -> Callable:
    """Build a DBAPI error handler with optional detail sanitization."""

    async def database_error_handler(_: Request, exc: DBAPIError) -> JSONResponse:
        logger.exception("Database error", exc_info=exc)

        detail = "Database error" if sanitize else _extract_database_detail(exc)

        if isinstance(exc, IntegrityError):
            return custom_exception_response(Conflict(detail))

        return JSONResponse(
            content={"successful": False, "detail": detail},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return database_error_handler


async def database_error_handler(_: Request, exc: DBAPIError) -> JSONResponse:
    """Default DBAPI error handler without detail sanitization."""
    logger.exception("Database error", exc_info=exc)

    detail = _extract_database_detail(exc)

    if isinstance(exc, IntegrityError):
        return custom_exception_response(Conflict(detail))

    return JSONResponse(
        content={"successful": False, "detail": detail},
        status_code=status.HTTP_400_BAD_REQUEST,
    )


async def database_not_found_handler(_: Request, exc: NoResultFound) -> JSONResponse:
    return JSONResponse(
        content={"successful": False, "detail": str(exc)},
        status_code=status.HTTP_404_NOT_FOUND,
    )
