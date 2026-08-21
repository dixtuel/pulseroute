import asyncio

import structlog
from sqlalchemy import select

from pulseroute.core.database import async_session_maker
from pulseroute.models.domain import CustomDomain
from pulseroute.services.domain_service import DomainService

logger = structlog.get_logger()


async def run_dns_verification_worker(interval_seconds: int = 300):
    """Periodically checks and auto-activates pending custom domains."""
    while True:
        try:
            async with async_session_maker() as db:
                unverified_domains = await db.execute(
                    select(CustomDomain).where(CustomDomain.is_verified.is_(False))
                )
                for domain in unverified_domains.scalars().all():
                    success, msg = await DomainService.verify_domain_dns(db, domain.id)
                    if success:
                        logger.info("domain_auto_verified", domain=domain.domain)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("dns_worker_error", error=str(e))
        await asyncio.sleep(interval_seconds)
