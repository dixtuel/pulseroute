import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from pulseroute.api.internal.caddy import router as caddy_router
from pulseroute.api.redirect import router as redirect_router
from pulseroute.api.v1 import api_v1_router
from pulseroute.core.config import settings
from pulseroute.core.database import init_db
from pulseroute.core.logging import setup_logging
from pulseroute.core.redis import close_redis
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
    description="⚡ Enterprise-Grade URL Shortener, Custom Domains & Real-Time Analytics Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/dashboard", response_class=HTMLResponse, tags=["Web Dashboard"])
async def render_dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "app_mode": settings.APP_MODE.value})


@app.get("/", response_class=HTMLResponse, tags=["Web Dashboard"])
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "app_mode": settings.APP_MODE.value})


# Mount Routers
app.include_router(api_v1_router)
app.include_router(caddy_router)
# Must be included last to catch /{slug}
app.include_router(redirect_router)
