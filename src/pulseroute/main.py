import asyncio
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
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

# Paths
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "web" / "templates"
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


app = FastAPI(
    title="PulseRoute API",
    description="Enterprise-Grade URL Shortener, Custom Domains & Real-Time Analytics Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

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


@app.get("/dashboard", response_class=HTMLResponse, tags=["Web Dashboard"])
async def render_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/privacy", response_class=HTMLResponse, tags=["Legal"])
async def render_privacy(request: Request):
    return templates.TemplateResponse(request=request, name="privacy.html")


@app.get("/terms", response_class=HTMLResponse, tags=["Legal"])
async def render_terms(request: Request):
    return templates.TemplateResponse(request=request, name="terms.html")


@app.get("/", response_class=HTMLResponse, tags=["Web Dashboard"])
async def root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


# Mount Routers
app.include_router(api_v1_router)
app.include_router(caddy_router)
# Must be included last to catch /{slug}
app.include_router(redirect_router)
