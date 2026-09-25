import base64
import hashlib
import hmac
import os
from typing import Any, Dict, Optional

import orjson
from cryptography.fernet import Fernet

from pulseroute.core.config import settings

DEFAULT_COOKIE_SECRET = "mikoshi-vds-shared-cookie-secret-key-2026"


def _get_fernet_key() -> bytes:
    # Derive a deterministic 32-byte URL-safe base64 key from SECRET_KEY
    key_hash = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(key_hash)


def encrypt_secret(plain_text: str) -> str:
    """Encrypts sensitive fields at rest (e.g. webhook secret keys, API tokens)."""
    if not plain_text:
        return ""
    f = Fernet(_get_fernet_key())
    return f.encrypt(plain_text.encode()).decode("utf-8")


def decrypt_secret(cipher_text: str) -> str:
    """Decrypts encrypted fields at rest."""
    if not cipher_text:
        return ""
    try:
        f = Fernet(_get_fernet_key())
        return f.decrypt(cipher_text.encode()).decode("utf-8")
    except Exception:
        return cipher_text


def encrypt_compact_cookie(data: Dict[str, Any], secret: Optional[str] = None) -> str:
    """
    Encrypts dictionary data into a compact, authenticated stream cipher token
    compatible with frontend ClientPerf / CompactCookie (v1_<iv>_<cipher>_<tag>).
    """
    key = (secret or DEFAULT_COOKIE_SECRET).encode("utf-8")
    plaintext = orjson.dumps(data)
    iv = os.urandom(4)

    keystream = bytearray()
    block_num = 0
    while len(keystream) < len(plaintext):
        h = hmac.new(key, iv + block_num.to_bytes(2, "big"), hashlib.sha256)
        keystream.extend(h.digest())
        block_num += 1

    ciphertext = bytes(p ^ k for p, k in zip(plaintext, keystream[:len(plaintext)]))
    tag = hmac.new(key, iv + ciphertext, hashlib.sha256).digest()[:8]

    return f"v1_{iv.hex()}_{ciphertext.hex()}_{tag.hex()}"


def decrypt_compact_cookie(token_str: str, secret: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Decrypts and verifies an authenticated compact cookie token.
    Returns parsed dict or None if invalid or tampered with.
    """
    if not token_str or not isinstance(token_str, str):
        return None
    parts = token_str.split("_")
    if len(parts) != 4 or parts[0] != "v1":
        return None
    try:
        iv = bytes.fromhex(parts[1])
        ciphertext = bytes.fromhex(parts[2])
        tag = bytes.fromhex(parts[3])
    except ValueError:
        return None

    if len(iv) != 4 or len(tag) != 8:
        return None

    key = (secret or DEFAULT_COOKIE_SECRET).encode("utf-8")
    expected_tag = hmac.new(key, iv + ciphertext, hashlib.sha256).digest()[:8]
    if not hmac.compare_digest(tag, expected_tag):
        return None

    keystream = bytearray()
    block_num = 0
    while len(keystream) < len(ciphertext):
        h = hmac.new(key, iv + block_num.to_bytes(2, "big"), hashlib.sha256)
        keystream.extend(h.digest())
        block_num += 1

    plaintext = bytes(c ^ k for c, k in zip(ciphertext, keystream[:len(ciphertext)]))
    try:
        return orjson.loads(plaintext)
    except Exception:
        return None


