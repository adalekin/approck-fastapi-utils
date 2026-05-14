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
| `approck_fastapi_utils.auth` | `ensure_current_user` dependency: reads `X-Jwt-Payload`, decodes base64 JSON, raises `Forbidden` if invalid |
| `approck_fastapi_utils.jwt` | `get_token_from_header`, `decode_payload` |
| `approck_fastapi_utils.exceptions` | `Unauthorized`, `Forbidden`, `NotFound`, `CustomException` |
| `approck_fastapi_utils.exception_handlers` | Handlers for `HTTPException` and custom exceptions |
| `approck_fastapi_utils.responses` | `SuccessfulResponse`, `FailedResponse`, OpenAPI-friendly `ResponseSchema` |
| `approck_fastapi_utils.response` | Prebuilt 404 response schema |
| `approck_fastapi_utils.types` | `CommaSeparatedList` for query parameters |
| `approck_fastapi_utils.sqlalchemy.exception_handlers` | Handlers for `DBAPIError` and `NoResultFound` (requires the `sqlalchemy` extra) |

## Usage

### Register exception handlers

Wire handlers once on the `FastAPI` app so `HTTPException` and library exceptions share the same JSON shape (`successful`, `detail`, and `code` for custom types).

```python
from fastapi import FastAPI, HTTPException

from approck_fastapi_utils.exception_handlers import custom_exception_handler, http_exception_handler
from approck_fastapi_utils.exceptions import CustomException

app = FastAPI()
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(CustomException, custom_exception_handler)
```

### `CustomException` in one breath

**Raise domain errors like normal Python exceptions — the client always gets the same JSON:** `successful: false`, **`code` = your class name** (great for UI/tests), `detail` = message. Built-ins map to HTTP for free: `Unauthorized` 401, `Forbidden` 403, `NotFound` 404; your own subclasses default to **400** unless you add a dedicated handler.

```python
from approck_fastapi_utils.exceptions import CustomException, NotFound

class OrderAlreadyPaid(CustomException):
    pass

raise OrderAlreadyPaid("already paid")  # -> 400 + code "OrderAlreadyPaid"
raise NotFound("missing")               # -> 404 + code "NotFound"
```

With the optional SQLAlchemy extra, register database errors the same way:

```python
from sqlalchemy.exc import DBAPIError, NoResultFound

from approck_fastapi_utils.sqlalchemy.exception_handlers import database_error_handler, database_not_found_handler

app.add_exception_handler(DBAPIError, database_error_handler)
app.add_exception_handler(NoResultFound, database_not_found_handler)
```

### JWT payload header (`ensure_current_user`)

`ensure_current_user` expects a header **`X-Jwt-Payload`** whose value is **URL-safe base64-encoded JSON** (for example the same JSON you would put in a JWT payload, without the signature segment). The dependency returns the decoded `dict` or raises `Forbidden`.

```python
from fastapi import APIRouter, Depends

from approck_fastapi_utils.auth import ensure_current_user
from approck_fastapi_utils.responses import SuccessfulResponse

router = APIRouter()

@router.get("/me")
async def read_me(payload: dict = Depends(ensure_current_user)):
    # use payload (e.g. "sub", roles) in your logic
    return SuccessfulResponse()
```

### Manual JWT helpers

Useful if you build another header scheme but still want the same parsing helpers.

```python
from approck_fastapi_utils.jwt import decode_payload, get_token_from_header

token = get_token_from_header(authorization)  # "Bearer <jwt>" -> "<jwt>"
claims = decode_payload(base64_payload_string)  # base64url JSON -> dict
```

### Standard JSON responses and OpenAPI examples

`SuccessfulResponse` / `FailedResponse` return `{"successful": true|false}`. Their `.schema()` helpers merge into route `responses` for OpenAPI; `HTTP_404_NOT_FOUND` is a ready-made 404 entry.

```python
from fastapi import APIRouter

from approck_fastapi_utils.response import HTTP_404_NOT_FOUND
from approck_fastapi_utils.responses import FailedResponse, SuccessfulResponse

router = APIRouter()

@router.get(
    "/health",
    responses={**SuccessfulResponse.schema(), **FailedResponse.schema(), **HTTP_404_NOT_FOUND},
)
async def health():
    return SuccessfulResponse()
```

### Comma-separated query lists

`CommaSeparatedList[T]` accepts a single comma-separated string (e.g. `?ids=1,2,3`) or repeated query values and validates elements as `T`.

```python
from typing import Annotated

from fastapi import APIRouter, Query

from approck_fastapi_utils.types import CommaSeparatedList

router = APIRouter()

@router.get("/items")
async def list_items(
    ids: Annotated[CommaSeparatedList[int], Query(description="Example: 1,2,3")],
):
    return {"ids": list(ids)}
```

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
