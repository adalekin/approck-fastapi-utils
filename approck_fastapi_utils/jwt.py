import base64
import json


def get_token_from_header(authorization):
    token = None

    if authorization:
        _, _, token = authorization.partition(" ")

    return token


def decode_payload(payload_string):
    return json.loads(base64.urlsafe_b64decode(payload_string + "=" * ((4 - len(payload_string) % 4) % 4)))
