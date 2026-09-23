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

    # Embedding Provider Configuration
    embedding_provider: str = "openai"
    embedding_api_key: str | None = None
    embedding_model: str = "text-embedding-3-small"
    embedding_base_url: str | None = None
    embedding_batch_size: int = 64

    # Qdrant Vector Database Configuration
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection_name: str = "sourcewise_documents"
    qdrant_vector_size: int = 1536
    qdrant_distance: str = "Cosine"
    qdrant_timeout: float = 10.0

    # LLM / Grounded Generation Configuration
    llm_provider: str = "openai"
    llm_api_key: str | None = None
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str | None = None
    llm_temperature: float = 0.0
    llm_max_tokens: int = 1024
    min_evidence_score: float = 0.0

    model_config = SettingsConfigDict(


        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
