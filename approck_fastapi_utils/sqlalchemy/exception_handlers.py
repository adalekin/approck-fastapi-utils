import logging
from collections.abc import Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, IntegrityError, NoResultFound

logger = logging.getLogger(__name__)


def _resolve_database_status_code(exc: DBAPIError) -> int:
    if isinstance(exc, IntegrityError):
        return status.HTTP_409_CONFLICT
    return status.HTTP_400_BAD_REQUEST


def _extract_database_detail(exc: DBAPIError) -> str:
    if exc.orig is not None:
        return str(exc.orig)
    return str(exc)


def create_database_error_handler(*, sanitize: bool = False) -> Callable:
    """Build a DBAPI error handler with optional detail sanitization."""

    async def database_error_handler(_: Request, exc: DBAPIError) -> JSONResponse:
        logger.exception("Database error", exc_info=exc)

        detail = "Database error" if sanitize else _extract_database_detail(exc)
        status_code = _resolve_database_status_code(exc)

        return JSONResponse(
            content={"successful": False, "detail": detail},
            status_code=status_code,
        )

    return database_error_handler


async def database_error_handler(_: Request, exc: DBAPIError) -> JSONResponse:
    """Default DBAPI error handler without detail sanitization."""
    logger.exception("Database error", exc_info=exc)

    return JSONResponse(
        content={"successful": False, "detail": _extract_database_detail(exc)},
        status_code=_resolve_database_status_code(exc),
    )


async def database_not_found_handler(_: Request, exc: NoResultFound) -> JSONResponse:
    return JSONResponse(
        content={"successful": False, "detail": str(exc)},
        status_code=status.HTTP_404_NOT_FOUND,
    )
