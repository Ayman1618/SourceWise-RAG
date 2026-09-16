"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings and environment configuration."""

    app_name: str = "SourceWise RAG API"
    app_version: str = "0.1.0"
    app_description: str = (
        "Backend API for SourceWise RAG — an evidence-first enterprise knowledge assistant."
    )
    app_env: str = "development"
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
