# approck-fastapi-utils

Small utilities for [FastAPI](https://fastapi.tiangolo.com/) services: JWT payload decoding from headers, standardized JSON responses, reusable exception handlers, a Pydantic-friendly comma-separated list type, and optional SQLAlchemy error handlers.

**Python:** 3.10+

## Install

From PyPI:

```bash
uv add approck-fastapi-utils
```

Or with pip:

```bash
pip install approck-fastapi-utils
```

Optional SQLAlchemy handlers:

```bash
uv add "approck-fastapi-utils[sqlalchemy]"
```

## What is included

| Module | Purpose |
|--------|---------|
| `approck_fastapi_utils` | Public re-exports of the most common symbols |
| `approck_fastapi_utils.auth` | `ensure_current_user`, `optional_current_user`, `ensure_current_superuser`, `JwtPayload` |
| `approck_fastapi_utils.jwt` | `encode_payload`, `decode_payload`, `get_token_from_header` |
| `approck_fastapi_utils.exceptions` | `CustomException` hierarchy with HTTP status codes |
| `approck_fastapi_utils.exception_handlers` | Handlers and `register_exception_handlers(profile=...)` |
| `approck_fastapi_utils.responses` | JSON responses and OpenAPI schema helpers |
| `approck_fastapi_utils.response` | Prebuilt 404 response schema |
| `approck_fastapi_utils.types` | `CommaSeparatedList` for query parameters |
| `approck_fastapi_utils.testing` | JWT/auth helpers for pytest |
| `approck_fastapi_utils.gateway` | `build_gateway_headers` for proxy routes |
| `approck_fastapi_utils.sqlalchemy.exception_handlers` | Handlers for `DBAPIError` and `NoResultFound` (requires the `sqlalchemy` extra) |

## Usage

### Register exception handlers

Use a preset instead of wiring handlers manually:

```python
from fastapi import FastAPI

from approck_fastapi_utils import register_exception_handlers

app = FastAPI()
register_exception_handlers(app, profile="api")
```

Profiles:

| Profile | Handlers |
|---------|----------|
| `minimal` | `HTTPException`, `CustomException` |
| `api` | `minimal` + `RequestValidationError`, `NoResultFound` |
| `internal` | `api` + `DBAPIError` (with optional `database_sanitize=True`) |

### `CustomException` and HTTP status codes

Built-in exceptions map to HTTP codes automatically. Subclasses can set `status_code` on the class or pass it to `__init__`:

```python
from approck_fastapi_utils import Conflict, CustomException, NotFound

class OrderAlreadyPaid(CustomException):
    status_code = 409

raise Conflict("already exists")          # -> 409
raise NotFound("missing")                   # -> 404
raise CustomException("bad", status_code=418)
```

Error body contract: `{"successful": false, "code": "...", "detail": "..."}`.

### JWT payload header

`ensure_current_user` reads **`X-JWT-Payload`** (URL-safe base64 JSON). Invalid payloads raise `Unauthorized` (401).

```python
from fastapi import APIRouter, Depends

from approck_fastapi_utils import ensure_current_user, optional_current_user
from approck_fastapi_utils.responses import SuccessfulResponse

router = APIRouter()

@router.get("/me")
async def read_me(payload: dict = Depends(ensure_current_user)):
    return SuccessfulResponse()

@router.get("/public")
async def public(payload: dict | None = Depends(optional_current_user())):
    ...
```

### JWT encode/decode

```python
from approck_fastapi_utils import decode_payload, encode_payload

payload = {"user_id": 1, "is_superuser": False}
encoded = encode_payload(payload)
claims = decode_payload(encoded)  # returns None on invalid input
```

### Testing helpers

```python
from approck_fastapi_utils.testing import auth_headers, override_current_user

headers = auth_headers(user_id=42, is_superuser=True)
override_current_user(app, user_id=42)
```

### Standard JSON responses and OpenAPI examples

```python
from approck_fastapi_utils import HTTP_404_NOT_FOUND, SuccessfulResponse, custom_exception_response_schema, error_response_schema
from approck_fastapi_utils.exceptions import NotFound

@router.get(
    "/health",
    responses={
        **SuccessfulResponse.schema(),
        **error_response_schema(400, "Bad request"),
        **custom_exception_response_schema(NotFound),
        **HTTP_404_NOT_FOUND,
    },
)
async def health():
    return SuccessfulResponse()
```

### Comma-separated query lists

`CommaSeparatedList[T]` accepts `?ids=1,2,3`. Whitespace is trimmed, empty string yields `[]`.

```python
from typing import Annotated

from fastapi import Query

from approck_fastapi_utils import CommaSeparatedList

ids: Annotated[CommaSeparatedList[int], Query(description="Example: 1,2,3")]
```

### Gateway/proxy headers

```python
from approck_fastapi_utils import build_gateway_headers

headers = build_gateway_headers(
    authorization=request.headers.get("Authorization"),
    x_jwt_payload=request.headers.get("X-JWT-Payload"),
)
```

## Breaking changes in 0.2.0

- Invalid `X-JWT-Payload` in `ensure_current_user` now raises `Unauthorized` (401) instead of `Forbidden` (403).
- `decode_payload` returns `None` instead of raising on invalid input.
- Header alias is explicitly `X-JWT-Payload`.

## Development

This repository uses [uv](https://docs.astral.sh/uv/).

```bash
uv sync --group dev --extra sqlalchemy
uv run ruff check .
uv run ruff format --check .
uv run mypy approck_fastapi_utils
uv run pytest
```

## License

MIT — see [LICENSE](LICENSE).

## Contributing

Issues and pull requests are welcome. Please run the checks above before submitting a change.
