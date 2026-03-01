"""FastAPI application factory and lifespan management."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from llm_deploy.config import settings
from llm_deploy.database import engine, Base
from llm_deploy.knowledge.loader import kb
from llm_deploy import models  # noqa: F401 — register all ORM models


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # Load hardware knowledge base
    kb.load()

    # Startup: create tables if using SQLite (dev mode)
    if "sqlite" in settings.DATABASE_URL:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: dispose engine
    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="LLM Deploy",
        description="大模型自助部署平台 API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    from llm_deploy.api.tasks import router as tasks_router
    from llm_deploy.api.models import router as models_router
    from llm_deploy.api.downloads import router as downloads_router

    app.include_router(tasks_router)
    app.include_router(models_router)
    app.include_router(downloads_router)

    @app.get("/api/health")
    async def health_check():
        return {"status": "ok", "version": "0.1.0"}

    return app


app = create_app()
