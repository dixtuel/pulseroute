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


async def run_dns_verification_worker(
    interval_seconds: int = 900,
    idle_sleep_seconds: int | None = 86400,
    max_pending_interval_seconds: int = 3600,
):
    """
    Checks and auto-activates pending custom domains.
    Optimized for serverless databases (Neon scale-to-zero):
    - When unverified domains exist: starts at 15 minutes and backs off to 1 hour
      until a new domain event arrives. These intervals leave room for Neon's
      5-minute scale-to-zero window between checks.
    - When NO unverified domains exist: waits for notify_unverified_domains_changed().
      A daily fallback also notices domains added from another process.
    """
    pending_interval = interval_seconds
    error_interval = 60
    while True:
        try:
            _pending_domain_event.clear()
            has_pending = False

            async with async_session_maker() as db:
                unverified_domains = await db.execute(select(CustomDomain).where(CustomDomain.is_verified.is_(False)))
                domain_list = unverified_domains.scalars().all()
                for domain in domain_list:
                    success, _ = await DomainService.verify_domain_dns(
                        db, domain.id, preloaded_domain=domain
                    )
                    if success:
                        logger.info("domain_auto_verified", domain=domain.domain)
                    else:
                        has_pending = True

            error_interval = 60

            # Sleep duration: active check if pending exists, deep sleep if none
            if not has_pending:
                pending_interval = interval_seconds
            if has_pending or idle_sleep_seconds is not None:
                sleep_duration = pending_interval if has_pending else idle_sleep_seconds
                try:
                    await asyncio.wait_for(_pending_domain_event.wait(), timeout=sleep_duration)
                except asyncio.TimeoutError:
                    if has_pending:
                        pending_interval = min(pending_interval * 2, max_pending_interval_seconds)
                else:
                    pending_interval = interval_seconds
            else:
                pending_interval = interval_seconds
                await _pending_domain_event.wait()

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("dns_worker_error", error=str(e))
            try:
                await asyncio.wait_for(_pending_domain_event.wait(), timeout=error_interval)
            except asyncio.TimeoutError:
                error_interval = min(error_interval * 2, 3600)
