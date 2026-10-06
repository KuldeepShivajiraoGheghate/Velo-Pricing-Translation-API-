"""
Velo — Pricing Translation API
FastAPI application entry point.
"""
import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import get_settings
from app.auth.router import router as auth_router
from app.public_api.router import router as public_api_router
from app.admin_api.router import router as admin_api_router

settings = get_settings()

# ── Structured logging setup ────────────────────────────────────────────────────
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(),
)
logger = structlog.get_logger()


# ── Application lifecycle ───────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown hooks."""
    logger.info("velo_starting", env=settings.app_env)
    yield
    logger.info("velo_shutdown")


# ── FastAPI app ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Velo — Pricing Translation API",
    description=(
        "Automatically translate SaaS pricing into local currencies and regulations."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS — allow dashboard frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routers ─────────────────────────────────────────────────────────────────────

app.include_router(auth_router, prefix="/api")
app.include_router(admin_api_router, prefix="/api")
app.include_router(public_api_router)


# ── Health check ────────────────────────────────────────────────────────────────

@app.get("/health", tags=["health"])
def health_check() -> dict:
    """
    Basic liveness check.
    Returns 200 with service status — used by Docker/load-balancer health probes.
    """
    return {
        "status": "ok",
        "service": "velo-api",
        "version": "1.0.0",
        "env": settings.app_env,
    }
