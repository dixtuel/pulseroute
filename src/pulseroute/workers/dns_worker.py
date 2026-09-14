import asyncio

import structlog
from sqlalchemy import select

from pulseroute.core.database import async_session_maker
from pulseroute.models.domain import CustomDomain
from pulseroute.services.domain_service import DomainService

logger = structlog.get_logger()

# Event triggered when a domain is added, updated or deleted
_pending_domain_event = asyncio.Event()


def notify_unverified_domains_changed():
    """Signals the DNS verification worker that unverified domains may be pending."""
    _pending_domain_event.set()


async def run_dns_verification_worker(interval_seconds: int = 300, idle_sleep_seconds: int = 3600):
    """
    Checks and auto-activates pending custom domains.
    Optimized for serverless databases (Neon scale-to-zero):
    - When unverified domains exist: checks every interval_seconds (default 300s).
    - When NO unverified domains exist: sleeps until notified via notify_unverified_domains_changed()
      or falls back to idle_sleep_seconds (default 3600s), allowing Neon compute to sleep.
    """
    while True:
        try:
            _pending_domain_event.clear()
            has_pending = False

            async with async_session_maker() as db:
                unverified_domains = await db.execute(select(CustomDomain).where(CustomDomain.is_verified.is_(False)))
                domain_list = unverified_domains.scalars().all()
                if domain_list:
                    has_pending = True
                    for domain in domain_list:
                        success, msg = await DomainService.verify_domain_dns(db, domain.id)
                        if success:
                            logger.info("domain_auto_verified", domain=domain.domain)

            # Sleep duration: active check if pending exists, deep sleep if none
            sleep_duration = interval_seconds if has_pending else idle_sleep_seconds
            try:
                await asyncio.wait_for(_pending_domain_event.wait(), timeout=sleep_duration)
            except asyncio.TimeoutError:
                pass

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("dns_worker_error", error=str(e))
            try:
                await asyncio.wait_for(_pending_domain_event.wait(), timeout=60)
            except asyncio.TimeoutError:
                pass
