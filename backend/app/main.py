"""Main application module for SourceWise RAG FastAPI backend."""

import uvicorn
from fastapi import FastAPI

from app.api.routes import health
from app.core.config import settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
    )

    # Register routers
    app.include_router(health.router)

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=(settings.app_env == "development"),
    )
