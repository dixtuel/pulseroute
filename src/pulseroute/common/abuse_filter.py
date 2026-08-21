from urllib.parse import urlparse

BLOCKED_DOMAINS = {
    "malware-traffic.com",
    "phishing-attack.net",
    "free-crypto-giveaway.xyz",
    "login-verify-account-fake.com",
}

BLOCKED_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".sh", ".scr", ".msi", ".apk", ".dmg", ".vbs"
}


def is_url_safe(url: str) -> tuple[bool, str]:
    """
    Validates URL safety for phishing, malware, and executable file blocks.
    Returns (is_safe: bool, reason: str)
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False, "Only HTTP and HTTPS protocols are allowed."

        hostname = (parsed.hostname or "").lower()
        if not hostname:
            return False, "Invalid hostname in URL."

        if hostname in BLOCKED_DOMAINS:
            return False, f"Domain '{hostname}' is blacklisted for security reasons."

        path = parsed.path.lower()
        for ext in BLOCKED_EXTENSIONS:
            if path.endswith(ext):
                return False, f"Executable and payload files ({ext}) are forbidden."

        return True, "Safe"
    except Exception as e:
        return False, f"Malformed URL: {e!s}"
