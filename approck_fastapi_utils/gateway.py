def build_gateway_headers(
    *,
    authorization: str | None = None,
    x_jwt_payload: str | None = None,
) -> dict[str, str]:
    """Build auth headers for gateway/proxy requests."""
    headers: dict[str, str] = {}

    if authorization:
        headers["Authorization"] = authorization
    if x_jwt_payload:
        headers["X-JWT-Payload"] = x_jwt_payload

    return headers
