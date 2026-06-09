class CustomException(Exception):
    """Domain exception mapped to a JSON error response by ``custom_exception_handler``."""

    status_code: int | None = None

    def __init__(self, message: str = "", *, status_code: int | None = None) -> None:
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code


class Unauthorized(CustomException):
    status_code = 401


class Forbidden(CustomException):
    status_code = 403


class NotFound(CustomException):
    status_code = 404


class Conflict(CustomException):
    status_code = 409


class UnprocessableEntity(CustomException):
    status_code = 422


class BadGateway(CustomException):
    status_code = 502


class ServiceUnavailable(CustomException):
    status_code = 503
