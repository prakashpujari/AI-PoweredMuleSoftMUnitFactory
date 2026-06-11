"""AI-MUnit-Factory — FastAPI application entry point."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    _PROMETHEUS_ENABLED = True
except ImportError:
    _PROMETHEUS_ENABLED = False

from app.api.routes import scan, munit, execution, coverage, failures, migration, dashboard, reports, auth
from app.config import get_settings
from app.database import create_tables
import app.models  # noqa: F401 — ensures all ORM models register with Base.metadata
from app.utils.exceptions import register_exception_handlers
from app.utils.logging import configure_logging, get_logger

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    logger.info("startup", app=settings.APP_NAME, version=settings.APP_VERSION, env=settings.APP_ENV)
    try:
        await create_tables()
        logger.info("database_ready")
    except Exception as exc:
        logger.warning("database_init_failed", error=str(exc))
    yield
    logger.info("shutdown", app=settings.APP_NAME)


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI-MUnit-Factory",
        description=(
            "Production-grade enterprise platform for automated MuleSoft MUnit test generation, "
            "execution, coverage analysis, failure root-cause analysis, and executive reporting."
        ),
        version=settings.APP_VERSION,
        docs_url=f"{settings.API_PREFIX}/docs",
        redoc_url=f"{settings.API_PREFIX}/redoc",
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware ────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # ── Exception Handlers ────────────────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ───────────────────────────────────────────────────────────────
    prefix = settings.API_PREFIX
    app.include_router(auth.router, prefix=prefix)
    app.include_router(scan.router, prefix=prefix)
    app.include_router(munit.router, prefix=prefix)
    app.include_router(execution.router, prefix=prefix)
    app.include_router(coverage.router, prefix=prefix)
    app.include_router(failures.router, prefix=prefix)
    app.include_router(migration.router, prefix=prefix)
    app.include_router(dashboard.router, prefix=prefix)
    app.include_router(reports.router, prefix=prefix)

    # ── Prometheus ────────────────────────────────────────────────────────────
    if _PROMETHEUS_ENABLED:
        Instrumentator().instrument(app).expose(app, endpoint="/metrics")

    # ── Health ────────────────────────────────────────────────────────────────
    @app.get("/health", tags=["health"])
    async def health() -> dict:
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
        }

    @app.get("/", tags=["root"])
    async def root() -> dict:
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": f"{settings.API_PREFIX}/docs",
        }

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
