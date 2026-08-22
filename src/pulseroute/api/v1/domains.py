from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.api.deps import require_authenticated_user, verify_workspace_access
from pulseroute.core.config import settings
from pulseroute.core.database import get_db
from pulseroute.models.domain import CustomDomain
from pulseroute.models.user import User
from pulseroute.schemas.domain import DomainCreate, DomainResponse, DomainVerifyResponse
from pulseroute.services.domain_service import DomainService

router = APIRouter(prefix="/domains", tags=["Custom Domains & DNS Onboarding"])


async def _get_domain_or_404(db: AsyncSession, domain_id: int) -> CustomDomain:
    domain = await db.get(CustomDomain, domain_id)
    if not domain or domain.workspace_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")
    return domain


@router.post("", response_model=DomainResponse, status_code=status.HTTP_201_CREATED)
async def add_custom_domain(
    domain_in: DomainCreate,
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    if not settings.ALLOW_CUSTOM_DOMAINS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Custom domains are disabled on this server by the administrator.",
        )

    await verify_workspace_access(domain_in.workspace_id, current_user, db, required_roles=("owner", "admin"))

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
    workspace_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_workspace_access(workspace_id, current_user, db)

    result = await db.execute(
        select(CustomDomain).where(CustomDomain.workspace_id == workspace_id).order_by(CustomDomain.created_at.desc())
    )
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
async def verify_custom_domain(
    domain_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    domain = await _get_domain_or_404(db, domain_id)
    await verify_workspace_access(domain.workspace_id, current_user, db, required_roles=("owner", "admin"))

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
async def delete_custom_domain(
    domain_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    domain = await _get_domain_or_404(db, domain_id)
    await verify_workspace_access(domain.workspace_id, current_user, db, required_roles=("owner", "admin"))

    await db.delete(domain)
    await db.commit()
