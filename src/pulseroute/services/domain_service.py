import secrets
from typing import Optional, Tuple

import dns.asyncresolver
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.core.config import settings
from pulseroute.models.domain import CustomDomain


class DomainService:
    @staticmethod
    def get_dns_instructions(domain_name: str, verification_code: str) -> dict:
        """
        Generates clean DNS setup instructions (Dub.co style):
        - Subdomains (e.g. go.acme.com) -> CNAME record
        - Apex/Root domains (e.g. acmelink.com) -> A record or TXT verification
        """
        parts = domain_name.split(".")
        is_subdomain = len(parts) > 2

        if is_subdomain:
            subdomain_prefix = parts[0]
            return {
                "type": "CNAME",
                "name": subdomain_prefix,
                "value": settings.CUSTOM_DOMAIN_CNAME_TARGET or settings.PRIMARY_DOMAIN.split(":")[0],
                "txt_fallback": {
                    "name": f"_pulseroute-challenge.{domain_name}",
                    "value": verification_code,
                },
                "instructions": f"Add a CNAME record with name '{subdomain_prefix}' pointing to '{settings.CUSTOM_DOMAIN_CNAME_TARGET}'.",
            }
        else:
            return {
                "type": "A",
                "name": "@",
                "value": "Your Server IP / CNAME Target",
                "txt_fallback": {
                    "name": f"_pulseroute-challenge.{domain_name}",
                    "value": verification_code,
                },
                "instructions": f"Add an A record pointing to your server IP, and a TXT record '_pulseroute-challenge.{domain_name}' with value '{verification_code}'.",
            }

    @staticmethod
    async def add_custom_domain(
        db: AsyncSession,
        domain_name: str,
        workspace_id: Optional[int] = None,
        custom_not_found_url: Optional[str] = None,
    ) -> CustomDomain:
        domain_clean = domain_name.strip().lower()
        if domain_clean.startswith(("http://", "https://")):
            domain_clean = domain_clean.split("://")[1].split("/")[0]

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
    async def verify_domain_dns(db: AsyncSession, domain_id: int) -> Tuple[bool, str]:
        result = await db.execute(select(CustomDomain).where(CustomDomain.id == domain_id))
        domain_obj = result.scalar_one_or_none()
        if not domain_obj:
            return False, "Domain not found"

        challenge_host = f"_pulseroute-challenge.{domain_obj.domain}"
        try:
            resolver = dns.asyncresolver.Resolver()
            resolver.timeout = 3.0
            resolver.lifetime = 3.0

            # 1. Check TXT record challenge
            answers = await resolver.resolve(challenge_host, "TXT")
            for rdata in answers:
                for txt_string in rdata.strings:
                    if domain_obj.verification_code.encode() in txt_string:
                        domain_obj.is_verified = True
                        await db.commit()
                        return True, "Domain successfully verified via DNS TXT challenge!"
        except Exception:
            pass

        # 2. Check CNAME record
        try:
            cname_answers = await resolver.resolve(domain_obj.domain, "CNAME")
            for rdata in cname_answers:
                target = str(rdata.target).rstrip(".")
                if target in (settings.CUSTOM_DOMAIN_CNAME_TARGET, settings.PRIMARY_DOMAIN.split(":")[0]):
                    domain_obj.is_verified = True
                    await db.commit()
                    return True, "Domain successfully verified via CNAME point!"
        except Exception:
            pass

        return False, "DNS records not yet propagated. Please check your DNS settings and try again in a few minutes."
