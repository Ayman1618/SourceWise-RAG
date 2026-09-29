"""Main application module for SourceWise RAG FastAPI backend."""

import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, query
from app.core.config import settings

# Configure structured production logging
logging.basicConfig(
    level=logging.INFO if settings.app_env == "production" else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
    )

    # Configure CORS dynamically from environment configuration
    origins = settings.allowed_cors_origins
    logger.info(
        "Configuring CORS middleware with %d origin(s): %s (env=%s)",
        len(origins),
        origins,
        settings.app_env,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health.router)
    app.include_router(query.router)

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.effective_port,
        reload=(settings.app_env == "development"),
    )

