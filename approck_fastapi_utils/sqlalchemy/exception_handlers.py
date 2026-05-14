from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, NoResultFound


async def database_error_handler(_: Request, exc: DBAPIError) -> JSONResponse:
    detail = str(exc.orig).split("DETAIL:  ")[-1].rstrip(".")
    return JSONResponse(
        content={"successful": False, "detail": detail},
        status_code=status.HTTP_400_BAD_REQUEST,
    )


async def database_not_found_handler(_: Request, exc: NoResultFound) -> JSONResponse:
    return JSONResponse(
        content={"successful": False, "detail": str(exc)},
        status_code=status.HTTP_404_NOT_FOUND,
    )
