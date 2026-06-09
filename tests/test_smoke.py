import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from approck_fastapi_utils import (
    CommaSeparatedList,
    Conflict,
    CustomException,
    Forbidden,
    NotFound,
    Unauthorized,
    build_gateway_headers,
    custom_exception_handler,
    decode_payload,
    encode_payload,
    ensure_current_superuser,
    ensure_current_user,
    optional_current_user,
    register_exception_handlers,
    resolve_custom_exception_status_code,
)
from approck_fastapi_utils.testing import auth_headers, make_jwt_payload_header, override_current_user


def test_imports() -> None:
    from approck_fastapi_utils import auth, exceptions, jwt, response, responses, types

    assert auth.ensure_current_user is not None
    assert exceptions.Forbidden is not None
    assert jwt.decode_payload is not None
    assert responses.SuccessfulResponse is not None
    assert response.HTTP_404_NOT_FOUND is not None
    assert types.CommaSeparatedList is not None


def test_sqlalchemy_subpackage_import() -> None:
    from approck_fastapi_utils.sqlalchemy import exception_handlers as sa_exc

    assert sa_exc.database_error_handler is not None
    assert sa_exc.create_database_error_handler is not None


def test_integrity_error_maps_to_conflict() -> None:
    import asyncio

    from sqlalchemy.exc import DBAPIError, IntegrityError

    from approck_fastapi_utils.sqlalchemy.exception_handlers import database_error_handler

    integrity_error = IntegrityError("INSERT INTO users", {}, Exception("Duplicate entry"))
    response = asyncio.run(database_error_handler(None, integrity_error))  # type: ignore[arg-type]
    assert response.status_code == 409
    assert response.body == b'{"successful":false,"detail":"Duplicate entry"}'

    generic_error = DBAPIError("SELECT 1", {}, Exception("syntax error"))
    response = asyncio.run(database_error_handler(None, generic_error))  # type: ignore[arg-type]
    assert response.status_code == 400


def test_encode_decode_payload_roundtrip() -> None:
    payload = {"user_id": 42, "is_superuser": True}
    encoded = encode_payload(payload)
    assert decode_payload(encoded) == payload


def test_decode_payload_invalid_returns_none() -> None:
    assert decode_payload(None) is None
    assert decode_payload("") is None
    assert decode_payload("not-valid-base64!!!") is None

    import base64
    import json

    array_payload = base64.urlsafe_b64encode(json.dumps([1, 2, 3]).encode()).decode().rstrip("=")
    assert decode_payload(array_payload) is None


def test_custom_exception_status_code_from_class() -> None:
    assert resolve_custom_exception_status_code(Conflict("busy")) == 409
    assert resolve_custom_exception_status_code(NotFound("missing")) == 404


def test_custom_exception_status_code_from_instance() -> None:
    class RateLimited(CustomException):
        pass

    exc = RateLimited("slow down", status_code=429)
    assert resolve_custom_exception_status_code(exc) == 429


@pytest.mark.parametrize(
    ("exception_cls", "expected_status"),
    [
        (Unauthorized, 401),
        (Forbidden, 403),
        (NotFound, 404),
        (Conflict, 409),
    ],
)
def test_custom_exception_handler_status_codes(
    exception_cls: type[CustomException],
    expected_status: int,
) -> None:
    app = FastAPI()
    app.add_exception_handler(CustomException, custom_exception_handler)

    @app.get("/raise")
    async def raise_exc() -> None:
        raise exception_cls("boom")

    response = TestClient(app).get("/raise")
    assert response.status_code == expected_status
    body = response.json()
    assert body["successful"] is False
    assert body["code"] == exception_cls.__name__
    assert body["detail"] == "boom"


def test_register_exception_handlers_validation_profile_api() -> None:
    app = FastAPI()
    register_exception_handlers(app, profile="api")

    @app.get("/items")
    async def items(ids: CommaSeparatedList[int]) -> dict:
        return {"ids": list(ids)}

    response = TestClient(app).get("/items", params={"ids": "not-int"})
    assert response.status_code == 422
    assert response.json()["code"] == "ValidationError"


def test_ensure_current_user_unauthorized_on_invalid_payload() -> None:
    app = FastAPI()
    register_exception_handlers(app, profile="minimal")

    @app.get("/me")
    async def me(payload: dict = Depends(ensure_current_user)) -> dict:
        return payload

    response = TestClient(app).get("/me", headers={"X-JWT-Payload": "broken"})
    assert response.status_code == 401


def test_ensure_current_user_accepts_valid_payload() -> None:
    app = FastAPI()

    @app.get("/me")
    async def me(payload: dict = Depends(ensure_current_user)) -> dict:
        return payload

    headers = auth_headers(user_id=7)
    response = TestClient(app).get("/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["user_id"] == 7


def test_optional_current_user_none_on_missing_header() -> None:
    app = FastAPI()

    @app.get("/maybe")
    async def maybe(payload: dict | None = Depends(optional_current_user())) -> dict:
        return {"payload": payload}

    assert TestClient(app).get("/maybe").json() == {"payload": None}


def test_optional_current_user_forbidden_on_invalid_payload() -> None:
    app = FastAPI()
    register_exception_handlers(app, profile="minimal")

    @app.get("/maybe")
    async def maybe(payload: dict | None = Depends(optional_current_user(on_invalid="forbidden"))) -> dict:
        return {"payload": payload}

    response = TestClient(app).get("/maybe", headers={"X-JWT-Payload": "broken"})
    assert response.status_code == 403


def test_ensure_current_superuser() -> None:
    app = FastAPI()
    register_exception_handlers(app, profile="minimal")

    @app.get("/admin")
    async def admin(payload: dict = Depends(ensure_current_superuser)) -> dict:
        return payload

    client = TestClient(app)
    assert client.get("/admin", headers=auth_headers(user_id=1, is_superuser=False)).status_code == 403
    assert client.get("/admin", headers=auth_headers(user_id=1, is_superuser=True)).status_code == 200


def test_override_current_user() -> None:
    app = FastAPI()
    override_current_user(app, user_id=99, role="tester")

    @app.get("/me")
    async def me(payload: dict = Depends(ensure_current_user)) -> dict:
        return payload

    assert TestClient(app).get("/me").json() == {"user_id": 99, "role": "tester"}


def test_make_jwt_payload_header() -> None:
    encoded = make_jwt_payload_header(user_id=3, is_superuser=True, sub="abc")
    assert decode_payload(encoded) == {"user_id": 3, "is_superuser": True, "sub": "abc"}


def test_build_gateway_headers() -> None:
    headers = build_gateway_headers(authorization="Bearer token", x_jwt_payload="payload")
    assert headers == {"Authorization": "Bearer token", "X-JWT-Payload": "payload"}


def test_comma_separated_list_empty_string() -> None:
    assert CommaSeparatedList[int].validate("") == []
    assert CommaSeparatedList[int].validate("  ") == []


def test_comma_separated_list_parsing() -> None:
    assert CommaSeparatedList[int].validate("1, 2,3") == [1, 2, 3]


def test_comma_separated_list_invalid_value_raises() -> None:
    with pytest.raises(ValidationError):
        CommaSeparatedList[int].validate("1,foo")
