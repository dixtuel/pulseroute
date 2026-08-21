import base64
import hashlib

from cryptography.fernet import Fernet

from pulseroute.core.config import settings


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
