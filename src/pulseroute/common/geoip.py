

def lookup_ip_location(ip: str) -> tuple[str, str, str]:
    """
    Returns (country_code: str, country_name: str, city: str)
    Mock / Fast GeoIP fallback with support for local / private ranges.
    """
    if not ip or ip.startswith(("127.", "192.168.", "10.", "172.16.", "::1", "localhost")):
        return "LOCAL", "Localhost / Private", "Localhost"

    # In production, can use maxminddb/GeoLite2 database if installed
    return "US", "United States", "San Francisco"
