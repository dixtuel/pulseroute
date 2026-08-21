import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from pulseroute.api.internal.caddy import router as caddy_router
from pulseroute.api.redirect import router as redirect_router
from pulseroute.api.v1 import api_v1_router
from pulseroute.core.config import settings
from pulseroute.core.database import init_db
from pulseroute.core.logging import setup_logging
from pulseroute.core.redis import close_redis
from pulseroute.core.security_middleware import SecurityHeadersMiddleware
from pulseroute.workers.analytics_worker import run_analytics_batch_worker
from pulseroute.workers.dns_worker import run_dns_verification_worker

# Paths
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "web" / "templates"
STATIC_DIR = BASE_DIR / "web" / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging(debug=settings.DEBUG)
    await init_db()

    # Start background workers as async tasks
    worker_tasks = []
    worker_tasks.append(asyncio.create_task(run_analytics_batch_worker()))
    worker_tasks.append(asyncio.create_task(run_dns_verification_worker()))

    yield

    # Shutdown
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

# Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# Custom HTML Exception Handlers for Web Browsers
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header and not request.url.path.startswith("/api/"):
        if exc.status_code == 404:
            return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
        elif exc.status_code == 410:
            return templates.TemplateResponse("410.html", {"request": request}, status_code=410)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/dashboard", response_class=HTMLResponse, tags=["Web Dashboard"])
async def render_dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "app_mode": settings.APP_MODE.value})


@app.get("/privacy", response_class=HTMLResponse, tags=["Legal"])
async def render_privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})


@app.get("/terms", response_class=HTMLResponse, tags=["Legal"])
async def render_terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})


@app.get("/", response_class=HTMLResponse, tags=["Web Dashboard"])
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "app_mode": settings.APP_MODE.value})


# Mount Routers
app.include_router(api_v1_router)
app.include_router(caddy_router)
# Must be included last to catch /{slug}
app.include_router(redirect_router)
