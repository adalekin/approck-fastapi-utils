from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from .exceptions import CustomException, NotFound, Unauthorized, Forbidden


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
    status_code_map = {
        Forbidden: status.HTTP_403_FORBIDDEN,
        NotFound: status.HTTP_404_NOT_FOUND,
        Unauthorized: status.HTTP_401_UNAUTHORIZED,
    }

    status_code = status.HTTP_400_BAD_REQUEST

    for base_exc, base_status_code in status_code_map.items():
        if isinstance(exc, base_exc):
            status_code = base_status_code

    response = JSONResponse(
        content={"successful": False, "code": exc.__class__.__name__, "detail": str(exc)}, status_code=status_code
    )

    return response
