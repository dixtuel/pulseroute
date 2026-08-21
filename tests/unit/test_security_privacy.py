from pulseroute.common.encryption import decrypt_secret, encrypt_secret
from pulseroute.common.privacy import anonymize_ip, generate_pseudonymous_visitor_id


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


def test_field_encryption_roundtrip():
    secret_text = "whsec_super_secret_webhook_key_123456"
    encrypted = encrypt_secret(secret_text)
    assert encrypted != secret_text
    decrypted = decrypt_secret(encrypted)
    assert decrypted == secret_text
