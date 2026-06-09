import base64
import json


def get_token_from_header(authorization: str | None) -> str | None:
    token = None

    if authorization:
        _, _, token = authorization.partition(" ")

    return token or None


def encode_payload(data: dict) -> str:
    """Encode a dict as URL-safe base64 JSON without padding."""
    raw = json.dumps(data, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_payload(payload_string: str | None) -> dict | None:
    """Decode URL-safe base64 JSON payload. Returns ``None`` on invalid input."""
    if not payload_string:
        return None

    try:
        padding = "=" * ((4 - len(payload_string) % 4) % 4)
        decoded = base64.urlsafe_b64decode(payload_string + padding)
        result = json.loads(decoded)
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return None

    if not isinstance(result, dict):
        return None

    return result
