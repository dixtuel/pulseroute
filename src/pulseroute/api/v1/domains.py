from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.core.database import get_db
from pulseroute.models.domain import CustomDomain
from pulseroute.schemas.domain import DomainCreate, DomainResponse, DomainVerifyResponse
from pulseroute.services.domain_service import DomainService

router = APIRouter(prefix="/domains", tags=["Custom Domains & DNS Onboarding"])


@router.post("", response_model=DomainResponse, status_code=status.HTTP_201_CREATED)
async def add_custom_domain(domain_in: DomainCreate, db: AsyncSession = Depends(get_db)):
    try:
        domain = await DomainService.add_custom_domain(
            db,
            domain_name=domain_in.domain,
            workspace_id=domain_in.workspace_id,
            custom_not_found_url=domain_in.custom_not_found_url
        )
        dns_guide = DomainService.get_dns_instructions(domain.domain, domain.verification_code)
        return {
            "id": domain.id,
            "domain": domain.domain,
            "verification_code": domain.verification_code,
            "is_verified": domain.is_verified,
            "created_at": domain.created_at,
            "custom_not_found_url": domain.custom_not_found_url,
            "dns_instructions": dns_guide,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[DomainResponse])
async def list_custom_domains(
    workspace_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(CustomDomain).order_by(CustomDomain.created_at.desc())
    if workspace_id:
        query = query.where(CustomDomain.workspace_id == workspace_id)
    result = await db.execute(query)
    domains = list(result.scalars().all())

    return [
        {
            "id": d.id,
            "domain": d.domain,
            "verification_code": d.verification_code,
            "is_verified": d.is_verified,
            "created_at": d.created_at,
            "custom_not_found_url": d.custom_not_found_url,
            "dns_instructions": DomainService.get_dns_instructions(d.domain, d.verification_code),
        }
        for d in domains
    ]


@router.post("/{domain_id}/verify", response_model=DomainVerifyResponse)
async def verify_custom_domain(domain_id: int, db: AsyncSession = Depends(get_db)):
    domain = await db.get(CustomDomain, domain_id)
    if not domain:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")

    is_verified, msg = await DomainService.verify_domain_dns(db, domain_id)
    dns_guide = DomainService.get_dns_instructions(domain.domain, domain.verification_code)

    return {
        "domain": domain.domain,
        "is_verified": is_verified,
        "status": "active" if is_verified else "pending_dns",
        "message": msg,
        "dns_instructions": dns_guide,
    }


@router.delete("/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_domain(domain_id: int, db: AsyncSession = Depends(get_db)):
    domain = await db.get(CustomDomain, domain_id)
    if not domain:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")
    await db.delete(domain)
    await db.commit()
