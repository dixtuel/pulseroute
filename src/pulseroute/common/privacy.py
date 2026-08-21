import hashlib
import ipaddress


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
