import base64
import hashlib
import hmac
import os
import zlib
from typing import Any, Dict, Optional

import orjson
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from pulseroute.core.config import settings

DEFAULT_COOKIE_SECRET = "mikoshi-vds-shared-cookie-secret-key-2026"
COMPRESSION_THRESHOLD_BYTES = 1024  # 1 KB: below this, compression adds CPU overhead and increases size


def _get_fernet_key() -> bytes:
    # Derive a deterministic 32-byte URL-safe base64 key from SECRET_KEY
    key_hash = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(key_hash)


def _get_aes_gcm_key(custom_secret: Optional[str] = None) -> bytes:
    # Derive a deterministic 32-byte key for AES-256-GCM
    secret = (custom_secret or settings.SECRET_KEY).encode("utf-8")
    return hashlib.sha256(secret).digest()


def secure_encode_payload(data: Any, secret: Optional[str] = None) -> str:
    """Safely serializes, selectively compresses (if >= 1KB), and encrypts using AES-256-GCM.

    Render Free-tier optimized:
      - Level-3 zlib (ultra-low CPU overhead on 0.1 vCPU).
      - AES-NI accelerated AEAD hardware instructions.
      - Never compresses <1KB payloads (avoids negative compression and CPU penalties).
    Output format: 'v2.<flags>.<nonce_b64>.<ciphertext_and_tag_b64>'
    """
    if data is None:
        return ""

    if isinstance(data, (dict, list)):
        raw_bytes = orjson.dumps(data)
    elif isinstance(data, str):
        raw_bytes = data.encode("utf-8")
    elif isinstance(data, bytes):
        raw_bytes = data
    else:
        raw_bytes = str(data).encode("utf-8")

    flags = 0
    # Compress only if at or above 1 KB to conserve Render 0.1 CPU and prevent negative expansion
    if len(raw_bytes) >= COMPRESSION_THRESHOLD_BYTES:
        compressed = zlib.compress(raw_bytes, level=3)
        if len(compressed) < len(raw_bytes):
            raw_bytes = compressed
            flags = 1

    key = _get_aes_gcm_key(secret)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit standard nonce for GCM

    # Authenticated encryption (ciphertext includes 128-bit authentication tag)
    ciphertext = aesgcm.encrypt(nonce, raw_bytes, None)

    nonce_b64 = base64.urlsafe_b64encode(nonce).decode("ascii")
    ct_b64 = base64.urlsafe_b64encode(ciphertext).decode("ascii")

    return f"v2.{flags}.{nonce_b64}.{ct_b64}"


def secure_decode_payload(payload_str: str, secret: Optional[str] = None, as_json: bool = True) -> Any:
    """Decrypts, verifies integrity (AEAD), and decompresses data encoded via secure_encode_payload.

    Constant-time authentication check prevents tampering and oracle attacks.
    Backward-compatible with legacy Fernet encrypted strings or raw JSON strings.
    """
    if not payload_str or not isinstance(payload_str, str):
        return None

    # 1. New v2 AES-256-GCM format
    if payload_str.startswith("v2."):
        parts = payload_str.split(".")
        if len(parts) != 4:
            return None
        try:
            flags = int(parts[1])
            nonce = base64.urlsafe_b64decode(parts[2])
            ciphertext = base64.urlsafe_b64decode(parts[3])
        except Exception:
            return None

        key = _get_aes_gcm_key(secret)
        aesgcm = AESGCM(key)
        try:
            decrypted = aesgcm.decrypt(nonce, ciphertext, None)
        except Exception:
            # Tampering detected, wrong key, or invalid tag -> return None safely without leaking details
            return None

        # Decompress if flag was set
        if flags == 1:
            try:
                decrypted = zlib.decompress(decrypted)
            except Exception:
                return None

        if as_json:
            try:
                return orjson.loads(decrypted)
            except Exception:
                return decrypted.decode("utf-8", errors="replace")
        return decrypted.decode("utf-8", errors="replace")

    # 2. Backward-compatibility: Legacy Fernet token (starts with 'gAAAAA')
    if payload_str.startswith("gAAAAA"):
        try:
            f = Fernet(_get_fernet_key())
            raw = f.decrypt(payload_str.encode()).decode("utf-8")
            if as_json:
                try:
                    return orjson.loads(raw)
                except Exception:
                    return raw
            return raw
        except Exception:
            return None

    # 3. Fallback: Raw unencrypted string or JSON
    if as_json:
        try:
            return orjson.loads(payload_str)
        except Exception:
            return payload_str

    return payload_str


def encrypt_secret(plain_text: str) -> str:
    """Encrypts sensitive fields at rest using AES-256-GCM."""
    if not plain_text:
        return ""
    return secure_encode_payload(plain_text)


def decrypt_secret(cipher_text: str) -> str:
    """Decrypts encrypted fields at rest (supports v2 AES-256-GCM and legacy Fernet)."""
    if not cipher_text:
        return ""
    res = secure_decode_payload(cipher_text, as_json=False)
    return str(res) if res is not None else cipher_text



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


