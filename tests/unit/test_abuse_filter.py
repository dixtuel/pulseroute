
from pulseroute.common.abuse_filter import is_url_safe, validate_link_targets
from pulseroute.core.config import settings


def test_safe_urls_pass():
    assert is_url_safe("https://google.com")[0] is True
    assert is_url_safe("https://github.com/dixtuel/pulseroute")[0] is True
    assert is_url_safe("http://example.org/page?query=123")[0] is True
    assert is_url_safe("https://en.wikipedia.org/wiki/URL")[0] is True


def test_ssrf_and_private_ips_blocked():
    # Loopback
    assert is_url_safe("http://127.0.0.1/admin")[0] is False
    assert is_url_safe("http://localhost:8000/api")[0] is False
    assert is_url_safe("http://[::1]/secret")[0] is False

    # Cloud metadata (AWS / GCP / DigitalOcean IMDS)
    assert is_url_safe("http://169.254.169.254/latest/meta-data/")[0] is False

    # Private IPv4 subnets
    assert is_url_safe("http://10.0.0.1/internal")[0] is False
    assert is_url_safe("http://192.168.1.100/router")[0] is False
    assert is_url_safe("http://172.16.0.5:5432")[0] is False

    # Internal domain suffixes
    assert is_url_safe("http://db.internal/query")[0] is False
    assert is_url_safe("http://server.local/status")[0] is False
    assert is_url_safe("http://gateway.lan")[0] is False


def test_embedded_credentials_blocked():
    # Classic phishing deceptive login vector
    assert is_url_safe("http://paypal.com@evil-phishing-host.xyz")[0] is False
    assert is_url_safe("https://admin:secret@malicious.com")[0] is False


def test_dangerous_payloads_and_executables_blocked():
    blocked = [
        "https://example.com/software.exe",
        "https://example.com/script.bat",
        "https://example.com/payload.cmd",
        "https://example.com/installer.msi",
        "https://example.com/dropper.scr",
        "https://example.com/macro.vbs",
        "https://example.com/disk.iso",
        "https://example.com/shell.ps1",
        "https://example.com/exploit.apk",
        "https://example.com/binary.dll",
    ]
    for url in blocked:
        is_safe, reason = is_url_safe(url)
        assert is_safe is False, f"Expected {url} to be blocked"
        assert "strictly forbidden" in reason or "payload" in reason


def test_double_extension_deception_blocked():
    assert is_url_safe("https://example.com/invoice.pdf.exe")[0] is False
    assert is_url_safe("https://example.com/receipt.xlsx.vbs")[0] is False
    assert is_url_safe("https://example.com/photo.jpg.scr")[0] is False


def test_known_malicious_domains_blocked():
    assert is_url_safe("https://malware-traffic.com/bad")[0] is False
    assert is_url_safe("http://phishing-attack.net/login")[0] is False
    assert is_url_safe("https://free-crypto-giveaway.xyz")[0] is False


def test_self_referencing_recursion_blocked():
    orig_primary = settings.PRIMARY_DOMAIN
    settings.PRIMARY_DOMAIN = "sely.tr"
    try:
        assert is_url_safe("https://sely.tr/loop-link")[0] is False
        assert is_url_safe("https://sub.sely.tr/nested")[0] is False
    finally:
        settings.PRIMARY_DOMAIN = orig_primary


def test_validate_link_targets_comprehensive():
    # All clean
    safe, err, field = validate_link_targets(
        destination_url="https://github.com",
        ios_destination="https://apps.apple.com/app/test",
        android_destination="https://play.google.com/store/apps/test",
        geo_targets={"TR": "https://sely.tr.clean.org", "US": "https://us.clean.org"},
        expired_url="https://clean-fallback.com",
    )
    assert safe is True
    assert err is None

    # Dirty iOS destination
    safe, err, field = validate_link_targets(
        destination_url="https://clean.com",
        ios_destination="http://127.0.0.1/admin",
    )
    assert safe is False
    assert field == "ios_destination"

    # Dirty Android destination
    safe, err, field = validate_link_targets(
        destination_url="https://clean.com",
        android_destination="https://example.com/malicious.apk",
    )
    assert safe is False
    assert field == "android_destination"

    # Dirty Geo Target
    safe, err, field = validate_link_targets(
        destination_url="https://clean.com",
        geo_targets={"TR": "https://clean-tr.com", "DE": "https://example.com/trojan.exe"},
    )
    assert safe is False
    assert "DE" in field
