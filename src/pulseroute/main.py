import asyncio
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text

from pulseroute.api.internal.caddy import router as caddy_router
from pulseroute.api.redirect import router as redirect_router
from pulseroute.api.v1 import api_v1_router
from pulseroute.core.config import settings
from pulseroute.core.database import async_session_maker, init_db
from pulseroute.core.logging import setup_logging
from pulseroute.core.redis import close_redis, get_redis
from pulseroute.core.security_middleware import SecurityHeadersMiddleware
from pulseroute.workers.analytics_worker import run_analytics_batch_worker
from pulseroute.workers.dns_worker import run_dns_verification_worker

# Paths & Multi-Directory Template Resolution
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "web" / "templates"
if not TEMPLATES_DIR.exists() or not (TEMPLATES_DIR / "index.html").exists():
    for candidate in [
        Path.cwd() / "src" / "pulseroute" / "web" / "templates",
        Path.cwd() / "web" / "templates",
        Path("/app/src/pulseroute/web/templates"),
        Path("/home/user/app/src/pulseroute/web/templates"),
    ]:
        if candidate.exists() and (candidate / "index.html").exists():
            TEMPLATES_DIR = candidate
            break
STATIC_DIR = BASE_DIR / "web" / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(debug=settings.DEBUG)
    await init_db()

    worker_tasks = []
    worker_tasks.append(asyncio.create_task(run_analytics_batch_worker()))
    worker_tasks.append(asyncio.create_task(run_dns_verification_worker()))

    yield

    for task in worker_tasks:
        task.cancel()
    await close_redis()


OPENAPI_DESCRIPTION = """
### ⚡ High-Frequency Link Dispatch, Custom Domains & Real-Time Telemetry Platform

PulseRoute is an open-source, enterprise-grade edge routing infrastructure designed for ultra-low latency link dispatch, multi-tenant workspace isolation, and privacy-preserving visitor analytics.

---

#### 🛡 Authentication & Security
* **JWT Bearer Token:** Include in headers: `Authorization: Bearer <your_jwt_token>` (obtained via `/api/v1/auth/login`).

---

#### 🚀 Key Features
1. **Sub-10ms Deterministic Redirects:** Distributed 64-bit Snowflake ID generation & Base62 encoding.
2. **Multi-Tenant Workspaces:** Strict row-level query filtering & RBAC (`owner`, `admin`, `member`).
3. **Automated Custom Domain TLS:** Instant Caddy On-Demand TLS handshake with DNS verification.
4. **Non-Blocking Telemetry:** Redis Stream ingestion with async batch persistence & GDPR/KVKK IP masking.
5. **Interstitial Countdown Pages:** Configurable delay page with a single, admin-configured platform-wide AdSense unit (no per-user monetization).
"""

TAGS_METADATA = [
    {
        "name": "Authentication",
        "description": "User registration, JWT session issuance, and `/me` profile inspection.",
    },
    {
        "name": "Workspaces & Tenant Isolation",
        "description": "Create isolated per-user workspaces and manage team membership roles.",
    },
    {
        "name": "Short Links & Routing",
        "description": "Dispatch high-performance short links, configure iOS/Android fallbacks, and manage UTM tags.",
    },
    {
        "name": "Telemetry & Analytics",
        "description": "Query live click streams, device architecture distribution, and geo-spatial analytics.",
    },
    {
        "name": "Custom Domains & TLS",
        "description": "Onboard branded domains with Caddy On-Demand TLS and automated DNS verification challenges. Requires login; the server administrator can disable onboarding entirely via `ALLOW_CUSTOM_DOMAINS`.",
    },
    {
        "name": "QR Engine",
        "description": "Render crisp vector SVG and high-DPI PNG QR codes with custom styling.",
    },
    {
        "name": "Abuse & Security",
        "description": "Malicious URL detection, phishing domain filters, and rate limit brute force jails.",
    },
    {
        "name": "Diagnostics",
        "description": "Live health checks, latency measurements, and database/Redis connection probes.",
    },
]

app = FastAPI(
    title="PulseRoute Enterprise Routing API",
    description=OPENAPI_DESCRIPTION,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=TAGS_METADATA,
    swagger_ui_parameters={
        "docExpansion": "list",
        "defaultModelsExpandDepth": 2,
        "syntaxHighlight.theme": "monokai",
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "filter": True,
    },
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# Health & Diagnostics
@app.get("/healthz", tags=["Diagnostics"])
async def health_check():
    start_time = time.time()
    db_ok = False
    redis_ok = False

    # Check DB
    try:
        async with async_session_maker() as db:
            await db.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        pass

    # Check Redis
    try:
        r = await get_redis()
        if r:
            await r.ping()
            redis_ok = True
    except Exception:
        pass

    elapsed_ms = round((time.time() - start_time) * 1000, 2)
    is_healthy = db_ok

    return JSONResponse(
        status_code=200 if is_healthy else 503,
        content={
            "status": "healthy" if is_healthy else "degraded",
            "version": "1.0.0",
            "database": "connected" if db_ok else "disconnected",
            "redis": "connected" if redis_ok else "disabled_or_unavailable",
            "latency_ms": elapsed_ms,
        }
    )


# Custom HTML Exception Handlers for Web Browsers
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header and not request.url.path.startswith("/api/"):
        if exc.status_code == 404:
            return templates.TemplateResponse(request=request, name="404.html", status_code=404)
        elif exc.status_code == 410:
            return templates.TemplateResponse(request=request, name="410.html", status_code=410)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/ads.txt", response_class=PlainTextResponse, tags=["Monetization"])
async def get_ads_txt():
    """Serves Google AdSense publisher verification ads.txt dynamically from env."""
    if settings.ADS_TXT_CONTENT:
        return PlainTextResponse(content=settings.ADS_TXT_CONTENT.strip(), media_type="text/plain")
    if settings.GLOBAL_ADSENSE_CLIENT_ID:
        pub_id = settings.GLOBAL_ADSENSE_CLIENT_ID.replace("ca-pub-", "pub-")
        return PlainTextResponse(content=f"google.com, {pub_id}, DIRECT, f08c47fec0942fa0\n", media_type="text/plain")
    raise HTTPException(status_code=404, detail="ads.txt is not configured on this instance.")


@app.get("/dashboard", response_class=HTMLResponse, tags=["Web Dashboard"])
async def render_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={
        "adsense_client_id": settings.GLOBAL_ADSENSE_CLIENT_ID,
        "require_custom_domain": settings.REQUIRE_CUSTOM_DOMAIN,
    })


@app.get("/privacy", response_class=HTMLResponse, tags=["Legal"])
async def render_privacy(request: Request):
    contact_user, _, contact_domain = (settings.OPERATOR_CONTACT_EMAIL or "").partition("@")
    return templates.TemplateResponse(request=request, name="privacy.html", context={
        "adsense_client_id": settings.GLOBAL_ADSENSE_CLIENT_ID,
        "operator_contact_user": contact_user or None,
        "operator_contact_domain": contact_domain or None,
        "primary_domain": settings.PRIMARY_DOMAIN,
    })


@app.get("/terms", response_class=HTMLResponse, tags=["Legal"])
async def render_terms(request: Request):
    return templates.TemplateResponse(request=request, name="terms.html", context={"adsense_client_id": settings.GLOBAL_ADSENSE_CLIENT_ID})


@app.get("/accessibility", response_class=HTMLResponse, tags=["Legal"])
async def render_accessibility(request: Request):
    contact_user, _, contact_domain = (settings.OPERATOR_CONTACT_EMAIL or "").partition("@")
    return templates.TemplateResponse(request=request, name="accessibility.html", context={
        "adsense_client_id": settings.GLOBAL_ADSENSE_CLIENT_ID,
        "operator_contact_user": contact_user or None,
        "operator_contact_domain": contact_domain or None,
        "primary_domain": settings.PRIMARY_DOMAIN,
    })


@app.get("/", response_class=HTMLResponse, tags=["Web Dashboard"])
async def root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={
        "adsense_client_id": settings.GLOBAL_ADSENSE_CLIENT_ID,
        "require_custom_domain": settings.REQUIRE_CUSTOM_DOMAIN,
    })


# Mount Routers
app.include_router(api_v1_router)
app.include_router(caddy_router)
# Must be included last to catch /{slug}
app.include_router(redirect_router)
