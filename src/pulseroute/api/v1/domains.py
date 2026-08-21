
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.core.config import settings
from pulseroute.core.database import get_db
from pulseroute.models.domain import CustomDomain
from pulseroute.schemas.domain import DomainCreate, DomainResponse, DomainVerifyResponse
from pulseroute.services.domain_service import DomainService

router = APIRouter(prefix="/domains", tags=["Custom Domains"])


@router.post("", response_model=DomainResponse, status_code=status.HTTP_201_CREATED)
async def add_custom_domain(domain_in: DomainCreate, db: AsyncSession = Depends(get_db)):
    try:
        domain = await DomainService.add_custom_domain(
            db, domain_name=domain_in.domain, custom_not_found_url=domain_in.custom_not_found_url
        )
        return domain
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=list[DomainResponse])
async def list_custom_domains(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CustomDomain).order_by(CustomDomain.created_at.desc()))
    return list(result.scalars().all())


@router.post("/{domain_id}/verify", response_model=DomainVerifyResponse)
async def verify_custom_domain(domain_id: int, db: AsyncSession = Depends(get_db)):
    domain = await db.get(CustomDomain, domain_id)
    if not domain:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")

    is_verified, msg = await DomainService.verify_domain_dns(db, domain_id)
    return {
        "domain": domain.domain,
        "is_verified": is_verified,
        "message": msg,
        "dns_txt_record": f"_pulseroute-challenge.{domain.domain} -> {domain.verification_code}",
        "cname_target": f"{domain.domain} -> {settings.CUSTOM_DOMAIN_CNAME_TARGET}",
    }
