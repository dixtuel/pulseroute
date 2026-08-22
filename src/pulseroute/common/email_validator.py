import dns.asyncresolver
import dns.resolver


async def email_domain_accepts_mail(email: str) -> bool:
    """
    Lightweight sanity check that an email's domain could plausibly receive mail --
    catches typo/garbage domains (e.g. user@asdkjhaskjdh) at registration time.

    Checks MX first, then falls back to A/AAAA per RFC 5321 (a domain with no MX
    record can still legally receive mail via its A record). Only rejects on a
    conclusive "this name doesn't exist / has neither record" result; any resolver
    error (timeout, temporary failure) fails open so transient DNS issues on the
    server never block a real signup.
    """
    domain = email.rsplit("@", 1)[-1].strip().lower()
    if not domain:
        return False

    resolver = dns.asyncresolver.Resolver()
    resolver.timeout = 3.0
    resolver.lifetime = 3.0

    try:
        await resolver.resolve(domain, "MX")
        return True
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        pass
    except Exception:
        return True  # resolver error (timeout etc.) -- fail open

    try:
        await resolver.resolve(domain, "A")
        return True
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        return False
    except Exception:
        return True  # resolver error (timeout etc.) -- fail open
