"""Pipeline service interfaces and implementations for SourceWise RAG."""

from app.services.chunking import ChunkingService
from app.services.embedding import BaseEmbeddingService, OpenAIEmbeddingService
from app.services.generation import BaseGenerationService, GroundedGenerationService
from app.models.indexing import IndexingFailure, IndexingResult
from app.services.indexing import (
    BaseIndexingService,
    DocumentIndexingService,
    IndexingError,
    run_indexing_cli,
)
from app.services.ingestion import (
    BaseIngestionService,
    DocumentIngestionService,
    run_ingestion_cli,
)
from app.services.markdown_parser import MarkdownParseError, MarkdownParser
from app.services.query import (
    BaseQueryOrchestrationService,
    QueryOrchestrationService,
)
from app.services.retrieval import BaseRetrievalService, QdrantRetrievalService
from app.services.vector_store import (
    BaseVectorStoreService,
    QdrantVectorStoreService,
    VectorSearchResult,
)

__all__ = [
    "BaseEmbeddingService",
    "BaseGenerationService",
    "BaseIndexingService",
    "BaseIngestionService",
    "BaseQueryOrchestrationService",
    "BaseRetrievalService",
    "BaseVectorStoreService",
    "ChunkingService",
    "DocumentIndexingService",
    "DocumentIngestionService",
    "GroundedGenerationService",
    "IndexingError",
    "IndexingFailure",
    "IndexingResult",
    "MarkdownParseError",
    "MarkdownParser",
    "OpenAIEmbeddingService",
    "QdrantRetrievalService",
    "QdrantVectorStoreService",
    "QueryOrchestrationService",
    "VectorSearchResult",
    "run_indexing_cli",
    "run_ingestion_cli",
]
