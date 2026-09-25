import ipaddress
import re
from typing import Any, Optional
from urllib.parse import unquote, urlparse

from pulseroute.core.config import settings

# 1. Known malicious, deceptive, and scam domains
BLOCKED_DOMAINS = {
    "malware-traffic.com",
    "phishing-attack.net",
    "free-crypto-giveaway.xyz",
    "login-verify-account-fake.com",
    "secure-login-update.com",
    "metamask-validate-wallet.net",
    "paypal-account-security-center.com",
    "appleid-device-locked.org",
    "binance-kyc-verification.top",
    "steam-community-free-skins.xyz",
}

# 2. Executable and hazardous binary payload extensions
BLOCKED_EXTENSIONS = {
    ".exe",
    ".bat",
    ".cmd",
    ".sh",
    ".scr",
    ".msi",
    ".apk",
    ".dmg",
    ".vbs",
    ".iso",
    ".img",
    ".vhd",
    ".dll",
    ".sys",
    ".ps1",
    ".vbe",
    ".hta",
    ".cpl",
    ".reg",
    ".jar",
    ".com",
    ".gadget",
    ".wsf",
    ".msc",
    ".bin",
    ".elf",
    ".deb",
    ".rpm",
}

# 3. Reserved or private hostnames that must never be targeted (SSRF defense)
BLOCKED_HOSTNAMES = {
    "localhost",
    "0.0.0.0",
    "127.0.0.1",
    "[::1]",
    "metadata.google.internal",
    "instance-data",
}

BLOCKED_HOSTNAME_SUFFIXES = (
    ".localhost",
    ".local",
    ".internal",
    ".lan",
    ".home",
    ".test",
    ".corp",
    ".intra",
)

# 4. Phishing keywords indicative of credential harvesting or scam impersonation
SUSPICIOUS_PHISHING_PATTERNS = [
    re.compile(r"(account|login|secure|verify|update|wallet|banking)-(support|auth|portal|signin|security)\.", re.IGNORECASE),
    re.compile(r"(metamask|phantom|trustwallet|binance|coinbase)-(verify|restore|seed)\.", re.IGNORECASE),
]


def _is_private_or_reserved_ip(ip_str: str) -> bool:
    """Checks if an IP address belongs to private, loopback, or metadata ranges."""
    try:
        ip = ipaddress.ip_address(ip_str.strip("[]"))
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local  # 169.254.169.254 AWS/GCP/DO cloud metadata
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        return False


def is_url_safe(url: str, check_recursion: bool = True) -> tuple[bool, str]:
    """
    Validates URL safety against phishing, malware, executable payloads, and SSRF attacks.
    Returns (is_safe: bool, reason: str)
    """
    if not url or not isinstance(url, str):
        return False, "URL cannot be empty."

    url = url.strip()
    if len(url) > 2048:
        return False, "URL exceeds maximum allowed length of 2048 characters."

    try:
        parsed = urlparse(url)
        if parsed.scheme.lower() not in ("http", "https"):
            return False, "Only HTTP and HTTPS protocols are allowed."

        # Reject embedded credentials in URLs (e.g. http://paypal.com@evil-site.com)
        if parsed.username or parsed.password:
            return False, "URLs containing embedded usernames or passwords are forbidden to prevent phishing."

        hostname = (parsed.hostname or "").lower().strip()
        if not hostname:
            return False, "Invalid or missing hostname in URL."

        # SSRF Check: Direct Hostname matches
        if hostname in BLOCKED_HOSTNAMES:
            return False, f"Destination hostname '{hostname}' is restricted (internal/loopback)."

        if any(hostname.endswith(suffix) for suffix in BLOCKED_HOSTNAME_SUFFIXES):
            return False, f"Destination hostname '{hostname}' belongs to a private/internal network domain."

        # SSRF Check: IP Address representation
        if _is_private_or_reserved_ip(hostname):
            return False, f"Direct access to private, loopback, or cloud-metadata IP addresses ({hostname}) is forbidden."

        # SSRF Check: Integer or hex IP bypass tricks (e.g., http://2130706433)
        if hostname.isdigit():
            return False, "Numeric IP formats are forbidden."

        # Recursive Shortening Defense (prevent loops or masking PulseRoute itself)
        if check_recursion:
            primary_host = (settings.PRIMARY_DOMAIN or "").split(":")[0].lower()
            if primary_host and (hostname == primary_host or hostname.endswith(f".{primary_host}")):
                return False, "Cannot create a short link pointing back to this service's own domain."

        # Domain Blacklist Check
        if hostname in BLOCKED_DOMAINS:
            return False, f"Domain '{hostname}' is blacklisted for confirmed security violations."

        # Double-extension or payload path checks
        path = unquote(parsed.path or "").lower()

        # Check blocked extensions
        for ext in BLOCKED_EXTENSIONS:
            if path.endswith(ext) or f"{ext}?" in url.lower() or f"{ext}#" in url.lower():
                return False, f"Executable and hazardous payload files ({ext}) are strictly forbidden."

        # Check double-extension deception (e.g. document.pdf.exe or invoice.xlsx.vbs)
        if re.search(r"\.(pdf|docx?|xlsx?|jpg|png|txt)\.(exe|scr|bat|vbs|cmd|ps1)$", path):
            return False, "Deceptive double file extension detected."

        # Heuristic Phishing Pattern Check
        for pattern in SUSPICIOUS_PHISHING_PATTERNS:
            if pattern.search(hostname):
                return False, "Destination URL matches known credential phishing patterns."

        return True, "Safe"

    except Exception as e:
        return False, f"Malformed URL or safety check error: {e!s}"


def validate_link_targets(
    destination_url: Optional[str] = None,
    ios_destination: Optional[str] = None,
    android_destination: Optional[str] = None,
    geo_targets: Optional[dict[str, Any]] = None,
    expired_url: Optional[str] = None,
) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Validates all potential destination URLs attached to a ShortLink.
    Returns (is_safe: bool, error_message: Optional[str], field_name: Optional[str])
    """
    if destination_url:
        safe, reason = is_url_safe(destination_url)
        if not safe:
            return False, f"Primary destination URL safety violation: {reason}", "destination_url"

    if ios_destination:
        safe, reason = is_url_safe(ios_destination)
        if not safe:
            return False, f"iOS destination URL safety violation: {reason}", "ios_destination"

    if android_destination:
        safe, reason = is_url_safe(android_destination)
        if not safe:
            return False, f"Android destination URL safety violation: {reason}", "android_destination"

    if expired_url:
        safe, reason = is_url_safe(expired_url)
        if not safe:
            return False, f"Expired fallback URL safety violation: {reason}", "expired_url"

    if geo_targets and isinstance(geo_targets, dict):
        for country_code, geo_url in geo_targets.items():
            if geo_url and isinstance(geo_url, str):
                safe, reason = is_url_safe(geo_url)
                if not safe:
                    return (
                        False,
                        f"Geo-targeting URL for '{country_code}' safety violation: {reason}",
                        f"geo_targets[{country_code}]",
                    )

    return True, None, None
