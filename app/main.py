from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.router import api_router
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.request_context import RequestContextMiddleware
from app.core.config import get_settings
from app.logging.logger import get_logger
from app.db.session import engine
from app.models import Base
import app.models.hiring_model  # noqa: F401 - registers hiring tables with SQLAlchemy metadata
from app.cache.redis_client import get_redis, close_redis
from app.workers.task_worker import start_worker, stop_worker


settings = get_settings()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} (env={settings.ENV})")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified")
    except Exception as _db_err:
        logger.warning(f"Database unavailable at startup: {_db_err}")
        logger.warning("Endpoints requiring DB will fail until PostgreSQL is reachable.")
        logger.warning("Run: alembic upgrade head  (after starting Postgres)")
    try:
        _r = await get_redis()
        await _r.ping()
        logger.info("Redis connection verified")
    except Exception as _redis_err:
        logger.warning(f"Redis unavailable at startup: {_redis_err}")
        logger.warning("Endpoints using @cache() will skip caching until Redis is reachable.")
    try:
        await start_worker()
        logger.info("Background worker started")
    except Exception as _worker_err:
        logger.warning(f"Background worker failed to start: {_worker_err}")
    yield
    await engine.dispose()
    logger.info("Database connection closed")
    await close_redis()
    logger.info("Redis connection closed")
    await stop_worker()
    logger.info("Background worker stopped")
    logger.info(f"{settings.APP_NAME} shutdown complete")


def create_app() -> FastAPI:
    prefix = settings.service_prefix  # e.g. "/payment-service"

    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        # All docs/schema URLs scoped under the service prefix
        docs_url=f"{prefix}/docs",
        redoc_url=f"{prefix}/redoc",
        openapi_url=f"{prefix}/openapi.json",
        lifespan=lifespan,
    )

    # Middlewares (registered outermost-first)
    # CORS goes first so the Next.js frontend (a different origin/port) can call this API
    # from the browser — curl/server-to-server calls don't need this, but real browser
    # fetch() calls are blocked without it.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3411",
            "http://127.0.0.1:3411",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # All API routes mounted under the service prefix
    # e.g. /payment-service/api/v1/users
    app.include_router(api_router, prefix=prefix)

    return app


app = create_app()
