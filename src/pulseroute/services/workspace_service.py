from typing import Optional

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseroute.models.link import ShortLink
from pulseroute.models.workspace import Workspace
from pulseroute.services.link_service import LinkService
from pulseroute.services.redirect_service import RedirectService


class WorkspaceService:
    @staticmethod
    async def delete_workspace(
        db: AsyncSession,
        redis_cli: Optional[aioredis.Redis],
        workspace: Workspace,
    ) -> None:
        """Permanently deletes a workspace and cascades all associated links,

        domains, webhooks, and analytics events. Also purges all cached routing
        keys from L1 in-memory LRU and L2 Redis to prevent stale redirects.
        """
        # 1. Fetch all short links belonging to this workspace
        links_res = await db.execute(select(ShortLink).where(ShortLink.workspace_id == workspace.id))
        links = list(links_res.scalars().all())

        # 2. Invalidate cache for each link
        for link in links:
            try:
                domain_name = await LinkService._link_domain_name(db, link)
                RedirectService.invalidate_l1(domain_name, link.slug)

                if redis_cli:
                    cache_key = LinkService._build_cache_key(domain_name, link.slug)
                    await redis_cli.delete(cache_key)
            except Exception:
                pass

        # 3. Delete workspace (cascades links, clicks, members, domains, webhooks)
        await db.delete(workspace)
        await db.commit()
