from fastapi import APIRouter

from pulseroute.api.v1.abuse import router as abuse_router
from pulseroute.api.v1.analytics import router as analytics_router
from pulseroute.api.v1.auth import router as auth_router
from pulseroute.api.v1.domains import router as domains_router
from pulseroute.api.v1.links import router as links_router
from pulseroute.api.v1.qr import router as qr_router
from pulseroute.api.v1.workspaces import router as workspaces_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(workspaces_router)
api_v1_router.include_router(links_router)
api_v1_router.include_router(domains_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(qr_router)
api_v1_router.include_router(abuse_router)
