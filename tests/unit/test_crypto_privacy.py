import hashlib
import hmac
import time

import orjson

from pulseroute.common.encryption import (
    decrypt_compact_cookie,
    decrypt_secret,
    encrypt_compact_cookie,
    encrypt_secret,
    secure_decode_payload,
    secure_encode_payload,
)
from pulseroute.common.privacy import (
    anonymize_ip,
    generate_pseudonymous_visitor_id,
    generate_reporter_fingerprint,
)

# --- Privacy & IP Anonymization ---

def test_ip_anonymization_ipv4():
    raw_ip = "198.51.100.45"
    anon_ip = anonymize_ip(raw_ip)
    assert anon_ip == "198.51.100.0"
    assert anon_ip != raw_ip


def test_ip_anonymization_ipv6():
    raw_ip = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    anon_ip = anonymize_ip(raw_ip)
    assert anon_ip.startswith("2001:db8:85a3:")


def test_pseudonymous_visitor_id():
    id1 = generate_pseudonymous_visitor_id("198.51.100.45", "Mozilla/5.0")
    id2 = generate_pseudonymous_visitor_id("198.51.100.99", "Mozilla/5.0")
    # Same subnet -> same pseudonymous hash
    assert id1 == id2
    assert len(id1) == 16


def test_abuse_report_fingerprint_is_keyed_and_signal_specific():
    args = {
        "client_ip": "198.51.100.45",
        "user_agent": "Example Browser/1.0",
        "accept_language": "en-US,en;q=0.9",
        "secret_key": "test-secret",
    }
    first = generate_reporter_fingerprint(**args)
    assert first == generate_reporter_fingerprint(**args)
    assert first != generate_reporter_fingerprint(**{**args, "secret_key": "another-secret"})
    assert first != generate_reporter_fingerprint(**{**args, "user_agent": "Other Browser/1"})
    assert len(first) == 64


# --- At-Rest Field Encryption (Fernet / AES-128-CBC + HMAC) ---

def test_field_encryption_roundtrip():
    secret_text = "whsec_super_secret_webhook_key_123456"
    encrypted = encrypt_secret(secret_text)
    assert encrypted != secret_text
    decrypted = decrypt_secret(encrypted)
    assert decrypted == secret_text


# --- Compact Authenticated Cookie Cipher (v1_<iv>_<ciphertext>_<tag>) ---

def test_compact_cookie_roundtrip():
    data = {"c": 1, "t": int(time.time())}
    token = encrypt_compact_cookie(data)
    assert token.startswith("v1_")
    parts = token.split("_")
    assert len(parts) == 4
    # IV: 4 bytes = 8 hex chars, Tag: 8 bytes = 16 hex chars
    assert len(parts[1]) == 8
    assert len(parts[3]) == 16

    decrypted = decrypt_compact_cookie(token)
    assert decrypted is not None
    assert decrypted["c"] == 1
    assert decrypted["t"] == data["t"]


def test_compact_cookie_custom_secret():
    custom_key = "custom-test-secret-key-for-cookie-cipher"
    data = {"c": 1, "custom": "field", "v": 42}
    token = encrypt_compact_cookie(data, secret=custom_key)

    # Decrypt with wrong secret should fail
    assert decrypt_compact_cookie(token, secret="wrong-secret") is None

    # Decrypt with correct secret should succeed
    decrypted = decrypt_compact_cookie(token, secret=custom_key)
    assert decrypted == data


def test_compact_cookie_tamper_detection():
    data = {"c": 1}
    token = encrypt_compact_cookie(data)
    parts = token.split("_")

    # Flip one byte in ciphertext
    ct_bytes = bytearray.fromhex(parts[2])
    ct_bytes[0] ^= 0x01
    tampered_token = f"v1_{parts[1]}_{ct_bytes.hex()}_{parts[3]}"
    assert decrypt_compact_cookie(tampered_token) is None

    # Tamper with tag
    tag_bytes = bytearray.fromhex(parts[3])
    tag_bytes[0] ^= 0xFF
    tampered_tag_token = f"v1_{parts[1]}_{parts[2]}_{tag_bytes.hex()}"
    assert decrypt_compact_cookie(tampered_tag_token) is None


def test_compact_cookie_malformed():
    assert decrypt_compact_cookie("") is None
    assert decrypt_compact_cookie("not_a_valid_token") is None
    assert decrypt_compact_cookie("v2_abcd_ef01_2345") is None
    assert decrypt_compact_cookie("v1_short_short_short") is None
    assert decrypt_compact_cookie("v1_invalidhex_invalidhex_invalidhex") is None


def test_cross_platform_parity():
    """Verify exact parity between Python and JS CompactCookie stream cipher algorithm."""
    secret = "mikoshi-vds-shared-cookie-secret-key-2026"
    fixed_iv = bytes.fromhex("1a2b3c4d")
    plaintext = orjson.dumps({"c": 1})

    key = secret.encode("utf-8")
    h = hmac.new(key, fixed_iv + (0).to_bytes(2, "big"), hashlib.sha256)
    keystream = h.digest()
    ciphertext = bytes(p ^ k for p, k in zip(plaintext, keystream[:len(plaintext)]))
    tag = hmac.new(key, fixed_iv + ciphertext, hashlib.sha256).digest()[:8]

    token = f"v1_{fixed_iv.hex()}_{ciphertext.hex()}_{tag.hex()}"
    decrypted = decrypt_compact_cookie(token, secret=secret)
    assert decrypted == {"c": 1}


# --- AES-256-GCM Smart Compression & AEAD Tampering Protection (Render Free-Tier Optimized) ---

def test_secure_payload_small_not_compressed():
    """Small payloads (<1KB) MUST NOT be compressed to prevent negative expansion and save CPU."""
    data = {"user_id": 42, "role": "owner", "workspace": "pulse"}
    encoded = secure_encode_payload(data)
    assert encoded.startswith("v2.")
    parts = encoded.split(".")
    assert len(parts) == 4
    # Flag 0 = uncompressed
    assert parts[1] == "0"

    decoded = secure_decode_payload(encoded)
    assert decoded == data


def test_secure_payload_large_is_compressed():
    """Large payloads (>=1KB) are compressed with zlib level-3 before AES-256-GCM encryption."""
    large_data = {
        "workspace_id": 1,
        "logs": ["click event registered for domain test.com with geo TR and chrome" for _ in range(50)],
        "meta": {"created_at": "2026-09-25T18:00:00Z"},
    }
    raw_size = len(orjson.dumps(large_data))
    assert raw_size > 1024

    encoded = secure_encode_payload(large_data)
    parts = encoded.split(".")
    # Flag 1 = compressed
    assert parts[1] == "1"

    decoded = secure_decode_payload(encoded)
    assert decoded == large_data


def test_secure_payload_tamper_detection():
    """Any modification in ciphertext or tag must cause secure_decode_payload to safely return None."""
    data = {"secret_note": "top_secret_information"}
    encoded = secure_encode_payload(data)
    parts = encoded.split(".")

    # Tamper ciphertext
    tampered = f"v2.{parts[1]}.{parts[2]}.aW52YWxpZA=="
    assert secure_decode_payload(tampered) is None

    # Tamper with wrong custom secret key
    assert secure_decode_payload(encoded, secret="wrong-secret-key-123") is None


def test_secure_payload_fallback_support():
    """Must safely handle raw json and malformed inputs without crashing."""
    assert secure_decode_payload("") is None
    assert secure_decode_payload(None) is None
    assert secure_decode_payload("not_a_valid_token") == "not_a_valid_token"

    # Plain JSON string
    plain_json = '{"direct": true}'
    assert secure_decode_payload(plain_json) == {"direct": True}


def test_get_client_preferences_server_side():
    """Verify backend get_client_preferences decrypts and validates client pr_pref cookie."""
    from unittest.mock import MagicMock

    from pulseroute.api.deps import get_client_preferences

    # 1. Valid cookie
    valid_token = encrypt_compact_cookie({"c": 1, "t": 1727280000})
    req = MagicMock()
    req.cookies = {"pr_pref": valid_token}
    res = get_client_preferences(req)
    assert res is not None
    assert res["c"] == 1

    # 2. Tampered cookie
    req.cookies = {"pr_pref": "v1_bad_token_bad"}
    assert get_client_preferences(req) is None

    # 3. Missing cookie
    req.cookies = {}
    assert get_client_preferences(req) is None

