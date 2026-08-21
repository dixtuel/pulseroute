from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.core.database import get_db
from pulseroute.models.domain import CustomDomain

router = APIRouter(prefix="/api/v1/internal", tags=["Internal Infrastructure"])


@router.get("/caddy-check")
async def caddy_on_demand_tls_check(
    domain: str = Query(..., description="Domain requested by incoming TLS handshake"),
    db: AsyncSession = Depends(get_db),
):
    """
    Called by Caddy On-Demand TLS 'ask' directive before issuing a Let's Encrypt certificate.
    Returns HTTP 200 if the domain is verified in PulseRoute, otherwise HTTP 403 Forbidden.
    """
    domain_clean = domain.strip().lower()
    result = await db.execute(
        select(CustomDomain).where(CustomDomain.domain == domain_clean, CustomDomain.is_verified.is_(True))
    )
    if result.scalar_one_or_none():
        return Response(status_code=status.HTTP_200_OK, content="OK")

    return Response(status_code=status.HTTP_403_FORBIDDEN, content="Domain not authorized")
