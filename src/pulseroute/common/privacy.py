import hashlib
import hmac
import ipaddress
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import Request


def extract_client_ip(request: "Request") -> str:
    """Read a valid Cloudflare client address or the ASGI client's trusted peer address.

    X-Forwarded-For and X-Real-IP are intentionally ignored because clients can supply them
    unless the reverse-proxy trust chain is configured explicitly.
    """
    candidates = [request.headers.get("cf-connecting-ip")]
    if request.client:
        candidates.append(request.client.host)
    for candidate in candidates:
        if not candidate:
            continue
        try:
            return ipaddress.ip_address(candidate.strip()).compressed
        except ValueError:
            continue
    return "0.0.0.0"


def generate_reporter_fingerprint(
    client_ip: str,
    user_agent: str = "",
    accept_language: str = "",
    secret_key: str = "",
) -> str:
    """
    Generates a secure, 1-way cryptographically salted fingerprint (HMAC-SHA256)
    from request-time signals (client IP, User-Agent, Accept-Language).
    Returns a keyed pseudonymous digest for short-window abuse deduplication. The digest is
    stored only on the report record and cleared after the configured dedupe window; raw UA,
    language, and full IP are never stored by this function.
    """
    if not secret_key:
        raise ValueError("SECRET_KEY is required to derive reporter fingerprints")
    key = secret_key.encode("utf-8")
    norm_ip = ipaddress.ip_address(client_ip).compressed
    norm_ua = user_agent.strip()[:256]
    norm_lang = accept_language.strip().split(",")[0][:32]
    payload = f"abuse-report-v1\0{norm_ip}\0{norm_ua}\0{norm_lang}".encode("utf-8")
    return hmac.new(key, payload, hashlib.sha256).hexdigest()


def anonymize_ip(ip: str) -> str:
    """
    Anonymizes IP address to comply with GDPR (EU) and KVKK (TR) privacy regulations.
    - IPv4: Sets the last octet to 0 (e.g. 192.168.1.123 -> 192.168.1.0)
    - IPv6: Sets the last 80 bits to 0
    """
    if not ip or ip in ("127.0.0.1", "localhost", "::1"):
        return "127.0.0.0"

    try:
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.version == 4:
            net = ipaddress.ip_network(f"{ip}/24", strict=False)
            return str(net.network_address)
        elif ip_obj.version == 6:
            net = ipaddress.ip_network(f"{ip}/48", strict=False)
            return str(net.network_address)
    except ValueError:
        pass

    return "0.0.0.0"


def generate_pseudonymous_visitor_id(ip: str, user_agent: str, salt: str = "pulseroute_kvkk_salt") -> str:
    """
    Generates a GDPR/KVKK-compliant 1-way pseudonymized visitor hash without storing cookies.
    """
    anon_ip = anonymize_ip(ip)
    payload = f"{anon_ip}|{user_agent}|{salt}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]
