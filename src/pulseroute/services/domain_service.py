import secrets

import dns.asyncresolver
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.core.config import settings
from pulseroute.models.domain import CustomDomain


class DomainService:
    @staticmethod
    async def add_custom_domain(
        db: AsyncSession,
        domain_name: str,
        workspace_id: int | None = None,
        custom_not_found_url: str | None = None
    ) -> CustomDomain:
        domain_clean = domain_name.strip().lower()
        # Check if domain already exists
        existing = await db.execute(select(CustomDomain).where(CustomDomain.domain == domain_clean))
        if existing.scalar_one_or_none():
            raise ValueError(f"Domain '{domain_clean}' is already registered.")

        challenge_code = f"pulseroute-verify={secrets.token_hex(16)}"
        domain_obj = CustomDomain(
            workspace_id=workspace_id,
            domain=domain_clean,
            verification_code=challenge_code,
            is_verified=False,
            custom_not_found_url=custom_not_found_url,
        )
        db.add(domain_obj)
        await db.commit()
        await db.refresh(domain_obj)
        return domain_obj

    @staticmethod
    async def verify_domain_dns(db: AsyncSession, domain_id: int) -> tuple[bool, str]:
        result = await db.execute(select(CustomDomain).where(CustomDomain.id == domain_id))
        domain_obj = result.scalar_one_or_none()
        if not domain_obj:
            return False, "Domain not found"

        challenge_host = f"_pulseroute-challenge.{domain_obj.domain}"
        try:
            resolver = dns.asyncresolver.Resolver()
            resolver.timeout = 3.0
            resolver.lifetime = 3.0

            # Check TXT record challenge
            answers = await resolver.resolve(challenge_host, "TXT")
            for rdata in answers:
                for txt_string in rdata.strings:
                    if domain_obj.verification_code.encode() in txt_string:
                        domain_obj.is_verified = True
                        await db.commit()
                        return True, "Domain successfully verified via DNS TXT challenge!"
        except Exception:
            pass

        # Also support CNAME fallback check
        try:
            cname_answers = await resolver.resolve(domain_obj.domain, "CNAME")
            for rdata in cname_answers:
                target = str(rdata.target).rstrip(".")
                if target == settings.CUSTOM_DOMAIN_CNAME_TARGET:
                    domain_obj.is_verified = True
                    await db.commit()
                    return True, "Domain successfully verified via CNAME point!"
        except Exception:
            pass

        return False, "DNS records not yet propagated or verification token mismatch."
