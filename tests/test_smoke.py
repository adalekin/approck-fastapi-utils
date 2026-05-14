"""Smoke tests so CI has at least one collected test."""

from approck_fastapi_utils import auth, exceptions, jwt, response, responses, types


def test_imports() -> None:
    assert auth.ensure_current_user is not None
    assert exceptions.Forbidden is not None
    assert jwt.decode_payload is not None
    assert responses.SuccessfulResponse is not None
    assert response.HTTP_404_NOT_FOUND is not None
    assert types.CommaSeparatedList is not None


def test_sqlalchemy_subpackage_import() -> None:
    from approck_fastapi_utils.sqlalchemy import exception_handlers as sa_exc

    assert sa_exc.database_error_handler is not None
