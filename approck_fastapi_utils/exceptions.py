class CustomException(Exception):
    pass


class Unauthorized(CustomException):
    pass


class Forbidden(CustomException):
    pass


class NotFound(CustomException):
    pass
