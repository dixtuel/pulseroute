"""Short-lived, encrypted tickets for browser redirect countdowns."""

import base64
import hashlib

import orjson
from cryptography.fernet import Fernet, InvalidToken

from pulseroute.core.config import settings


def _cipher() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())
    return Fernet(key)


def issue_ticket(payload: dict) -> str:
    return _cipher().encrypt(orjson.dumps(payload)).decode()


def read_ticket(token: str) -> dict | None:
    if not isinstance(token, str):
        return None
    try:
        payload = orjson.loads(_cipher().decrypt(token.encode(), ttl=600))
        return payload if isinstance(payload, dict) else None
    except (InvalidToken, ValueError, TypeError, orjson.JSONDecodeError):
        return None
