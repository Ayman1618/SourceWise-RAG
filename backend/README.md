# SourceWise RAG — Backend Service

Backend service for SourceWise RAG, an evidence-first enterprise knowledge assistant designed to retrieve, verify, and cite internal documentation passages.

---

## Purpose

The backend provides the API infrastructure, data models, vector storage layer, and pipeline services for SourceWise RAG:
- **Foundational Architecture:** FastAPI application setup, structured configuration via Pydantic Settings, modular router layout, and health checks.
- **RAG Pipeline Contracts:** Typed Pydantic data models establishing strict provenance and citation traceability between documents, chunks, retrieved evidence, citations, and generated answers.
- **Embedding Foundation:** Provider-agnostic embedding interface (`BaseEmbeddingService`) and OpenAI-compatible implementation (`OpenAIEmbeddingService`) supporting custom models and local endpoints.
- **Qdrant Vector Store:** Vector database abstraction (`BaseVectorStoreService`) and Qdrant implementation (`QdrantVectorStoreService`) managing collection lifecycle, deterministic point indexing, and payload preservation.

---

## Technology Stack

- **Runtime:** Python 3.10+ (Recommended: Python 3.12)
- **Web Framework:** [FastAPI](https://fastapi.tiangolo.com/) (0.110+)
- **ASGI Server:** [Uvicorn](https://www.uvicorn.org/) (0.28+)
- **Vector Database Client:** [qdrant-client](https://github.com/qdrant/qdrant-client) (1.8+)
- **LLM/Embedding Client:** [openai](https://github.com/openai/openai-python) (1.0+)
- **Data Validation & Settings:** [Pydantic v2](https://docs.pydantic.dev/) & [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- **Testing:** [pytest](https://docs.pytest.org/) (8.0+) / `unittest`

---

## Project Structure

```
backend/
├── app/
│   ├── __init__.py           # Application package definition
│   ├── main.py               # FastAPI application initialization & factory
│   ├── api/
│   │   ├── __init__.py       # API router package
│   │   └── routes/
│   │       ├── __init__.py   # Route handlers package
│   │       └── health.py     # Health check endpoint (/health)
│   ├── core/
│   │   ├── __init__.py       # Core package
│   │   └── config.py         # Application settings via Pydantic Settings
│   ├── models/
│   │   ├── __init__.py       # Data models package re-exports
│   │   ├── document.py       # Normalized Document model
│   │   ├── chunk.py          # Extracted text Chunk model with parent provenance
│   │   ├── retrieval.py      # RetrievedChunk, RetrievalQuery, RetrievalResult
│   │   ├── citation.py       # Verifiable Citation model
│   │   ├── generation.py     # Grounded Answer model & EvidenceStatus enum
│   │   └── health.py         # Health check response schema
│   └── services/
│       ├── __init__.py       # Pipeline service interface & implementation exports
│       ├── markdown_parser.py# Markdown YAML frontmatter parser & normalizer
│       ├── chunking.py       # Markdown-aware ChunkingService (500-800 tok, 50-100 overlap)
│       ├── ingestion.py      # BaseIngestionService contract & DocumentIngestionService
│       ├── embedding.py      # BaseEmbeddingService & OpenAIEmbeddingService
│       ├── vector_store.py   # BaseVectorStoreService, QdrantVectorStoreService, VectorSearchResult
│       ├── retrieval.py      # BaseRetrievalService & QdrantRetrievalService
│       └── generation.py     # BaseGenerationService & GroundedGenerationService
├── tests/
│   ├── __init__.py           # Test suite package
│   ├── test_ingestion_chunking.py # Ingestion, chunking, overlap & boundary tests
│   ├── test_models.py        # Model validation and traceability tests
│   ├── test_embedding.py     # Embedding service contracts & OpenAI mock tests
│   ├── test_vector_store.py  # Vector store contracts & Qdrant mock tests
│   ├── test_retrieval.py     # Semantic retrieval service & filtering tests
│   ├── test_generation.py    # Grounded generation, citation validation & refusal tests
│   └── test_services.py      # Service interface contracts and re-exports

├── requirements.txt          # Python dependencies
├── .env.example              # Example environment configuration
└── README.md                 # Backend documentation
```

---

## Core RAG Contracts & Traceability

SourceWise RAG is an **evidence-first** system. Every generated answer must be backed by verifiable citations that map directly back to the original source passage.

### Traceability Chain

```
Document (Normalized source file + enterprise metadata)
   │
   ▼
Chunk (Extracted text segment retaining document_id)
   │
   ▼
Vector Point in Qdrant (Embedding vector + metadata payload)
   │
   ▼
RetrievedChunk (Ranked & scored candidate evidence)
   │
   ▼
Citation (Verifiable citation mapping passage → chunk_id → document_id)
   │
   ▼
Answer (Grounded answer payload delivered to the client)
```

### Vector Payload Schema

When chunks are stored in Qdrant, each point preserves the entire lineage required for precise citation attribution:

```json
{
  "chunk_id": "doc_runbook_v1#chunk_0",
  "document_id": "doc_runbook_v1",
  "text": "Extracted text segment from the original document.",
  "chunk_index": 0,
  "token_count": 42,
  "metadata": {
    "title": "Production Incident Runbook",
    "filepath": "ops/runbooks/incident.md",
    "source": "confluence",
    "tags": ["ops", "production"]
  }
}
```

Point IDs in Qdrant are generated deterministically as UUIDv5 hashes of `chunk_id`, guaranteeing idempotent upserts during re-indexing.

---

## Pipeline Services

- **`BaseEmbeddingService` / `OpenAIEmbeddingService`** (`embed_text`, `embed_texts`, `query_embedding`):
  Generates dense vector representations using OpenAI or any OpenAI-compatible provider (e.g. Ollama, LiteLLM, Azure).
- **`BaseVectorStoreService` / `QdrantVectorStoreService`** (`connect`, `collection_exists`, `create_collection_if_not_exists`, `store_chunks`, `search`, `close`):
  Connects to Qdrant, provisions collections, performs similarity searches with metadata filtering, and stores chunk vectors with full provenance payloads.
- **`BaseRetrievalService` / `QdrantRetrievalService`** (`retrieve`):
  Coordinates query embedding generation, similarity search via `BaseVectorStoreService`, metadata filtering (e.g. `product`, `department`, `document_id`), and output reconstruction into ranked `RetrievedChunk` items.
- **`BaseIngestionService` / `DocumentIngestionService`** (`ingest`, `chunk_document`, `ingest_and_chunk`):
  Parses Markdown documents with YAML frontmatter and segments them into discrete, traceable chunks.
- **`BaseGenerationService` / `GroundedGenerationService`** (`generate`):
  Synthesizes factually grounded answers from retrieved evidence, enforces strict refusal on insufficient/unsupported information, and constructs verifiable `Citation` objects mapped directly to source chunks.

---

## Grounded Answer Generation & Citations

SourceWise RAG implements an **evidence-first generation pipeline** designed to prevent hallucinations and provide complete auditability.

```
User Question + Retrieved Chunks
               │
               ▼
   [GroundedGenerationService]
               │
               ├── 1. Zero/Low Evidence Check:
               │      If no evidence or filtered out → Refusal ("I couldn't find sufficient...")
               │
               ├── 2. Strict Grounding System Prompt:
               │      - Answer using ONLY provided evidence
               │      - No outside knowledge or speculation
               │      - Structured JSON output with cited chunk_id
               │
               ├── 3. LLM Generation (OpenAI-compatible)
               │
               └── 4. Citation Verification & Construction:
                      - Match cited chunk_id against retrieved chunks
                      - Reject hallucinated/unmatched chunk IDs
                      - If model claims support but citations are invalid → REFUSED
                      - Build traceable Citations: document_id, chunk_id, passage, source_path, score
               │
               ▼
   Grounded Answer Object (query, answer, citations, evidence_status)
```

### Evidence Sufficiency & Refusal Policy

- **`EvidenceStatus.INSUFFICIENT`**: There is not enough evidence to answer the query (e.g., zero chunks retrieved, evidence pre-filtered, or model analysis indicates insufficient information in the knowledge base). The standard refusal notice is returned.
- **`EvidenceStatus.REFUSED`**: Evidence was supplied, but the generated answer or citations could not be safely validated (e.g., all cited IDs were hallucinated or failed validation).
- **`EvidenceStatus.SUFFICIENT`**: The answer is completely backed by verified citations pointing to real retrieved chunks.

---

## Configuration & Environment Variables

All settings are configured via environment variables or a `.env` file using Pydantic Settings.

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | Environment name (`development`, `production`, `test`) |
| `BACKEND_HOST` | `127.0.0.1` | Host address for FastAPI server |
| `BACKEND_PORT` | `8000` | Port for FastAPI server |
| `EMBEDDING_PROVIDER` | `openai` | Embedding provider identifier |
| `EMBEDDING_API_KEY` | `None` | API key for OpenAI or compatible embedding provider |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Model name used for embedding generation |
| `EMBEDDING_BASE_URL` | `None` | Custom base URL for OpenAI-compatible proxies/local servers |
| `EMBEDDING_BATCH_SIZE` | `64` | Maximum texts per embedding batch request |
| `QDRANT_URL` | `http://localhost:6333` | Endpoint URL of the Qdrant vector database |
| `QDRANT_API_KEY` | `None` | Optional API key for authenticated Qdrant instances |
| `QDRANT_COLLECTION_NAME` | `sourcewise_documents` | Target collection name for chunk vectors |
| `QDRANT_VECTOR_SIZE` | `1536` | Vector dimension size matching embedding model |
| `QDRANT_DISTANCE` | `Cosine` | Distance metric for similarity (`Cosine`, `Dot`, `Euclid`) |
| `QDRANT_TIMEOUT` | `10.0` | Connection timeout in seconds |
| `LLM_PROVIDER` | `openai` | LLM generation provider identifier |
| `LLM_API_KEY` | `None` | API key for OpenAI or compatible LLM provider |
| `LLM_MODEL` | `gpt-4o-mini` | Generation model name (e.g. OpenAI, Ollama, LiteLLM) |
| `LLM_BASE_URL` | `None` | Custom base URL for OpenAI-compatible LLM endpoints |
| `LLM_TEMPERATURE` | `0.0` | Generation sampling temperature (0.0 for deterministic grounding) |
| `LLM_MAX_TOKENS` | `1024` | Maximum output tokens for answer generation |
| `MIN_EVIDENCE_SCORE` | `0.0` | Optional retrieval score threshold for pre-filtering evidence |


---

## Document Ingestion & Chunking Pipeline

The ingestion and chunking pipeline processes raw Markdown knowledge documents into canonical `Document` objects and segments them into discrete, citation-ready `Chunk` objects.

```
Raw Markdown (with YAML Frontmatter)
            │
            ▼
    [MarkdownParser]
            │   ├── Extracts frontmatter metadata & strips delimiters
            │   ├── Infers title from `# Heading` if missing
            │   └── Generates slugified document_id fallback
            ▼
   Canonical Document
            │
            ▼
    [ChunkingService]
            │   ├── Markdown-aware boundary splitting (headers, paragraphs, code blocks)
            │   ├── Targets 500–800 tokens per chunk
            │   ├── Preserves 50–100 token overlap across sentence boundaries
            │   └── Generates deterministic chunk_id: {document_id}#chunk_{index}
            ▼
   Traceable Chunks (Preserving document_id & source metadata)
```

### Key Components

1. **`MarkdownParser` (`app/services/markdown_parser.py`)**:
   - Parses YAML frontmatter headers delimited by `---` using `yaml.safe_load`.
   - Maps standard metadata fields (`document_id`, `title`, `source_type`, `product`, `version`, `department`, `owner`, `last_updated`, `access_level`, `language`).
   - Normalizes any non-standard frontmatter keys into the `metadata` dictionary.
   - **Title Fallback**: If `title` is missing in frontmatter, extracts the first level-1 Markdown heading (`# Heading`). If no heading exists, falls back to the file stem.
   - **Document ID Fallback**: If `document_id` is missing in frontmatter, derives a deterministic slug from the source file stem.
   - **Error Handling**: Raises `MarkdownParseError` on invalid YAML syntax, missing delimiters, or empty document bodies.

2. **`ChunkingService` (`app/services/chunking.py`)**:
   - **Semantic Boundaries**: Splits content along Markdown headers (`#`, `##`, `###`), blank lines, and paragraphs. Keeps fenced code blocks (` ```...``` `) intact unless an individual block exceeds the maximum token window.
   - **Token Windows**: Configurable with defaults targeting **500–800 tokens** per chunk.
   - **Context Overlap**: Configurable with defaults targeting **50–100 tokens** of overlap between adjacent chunks, aligned to sentence boundaries.
   - **Deterministic IDs**: Generates consistent identifiers in the format `{document_id}#chunk_{chunk_index}`.
   - **Lineage & Provenance**: Every chunk preserves `document_id`, sequential `chunk_index`, estimated `token_count`, and inherits parent metadata (`title`, `source_path`, `version`, `access_level`, etc.).

3. **`DocumentIngestionService` (`app/services/ingestion.py`)**:
   - Concrete implementation of `BaseIngestionService`.
   - `ingest(source)`: Accepts directory paths (e.g., `data/sample-documents/`), individual file paths, raw Markdown text strings, or dictionary payloads.
   - `chunk_document(document)`: Delegates to `ChunkingService` to produce child chunks.
   - `ingest_and_chunk(source)`: Convenience method that ingests documents and chunks them in a single call.

### Usage Example

```python
import asyncio
from pathlib import Path
from app.services.ingestion import DocumentIngestionService

async def main():
    service = DocumentIngestionService()

    # Ingest all sample documents from data/sample-documents/
    sample_dir = Path("data/sample-documents")
    documents, chunks = await service.ingest_and_chunk(sample_dir)

    print(f"Ingested {len(documents)} documents, produced {len(chunks)} chunks.")

    for chunk in chunks[:3]:
        print(f"Chunk ID: {chunk.chunk_id}")
        print(f"Parent Doc: {chunk.document_id}")
        print(f"Tokens: {chunk.token_count}")
        print(f"Title: {chunk.metadata.get('title')}")
        print(f"Text snippet: {chunk.text[:100]}...\n")

if __name__ == "__main__":
    asyncio.run(main())
```

#### CLI Ingestion Runner

You can also run the ingestion and chunking pipeline directly from the command line:

```bash
# Run against default sample documents (data/sample-documents/)
python run_ingestion.py

# Or specify a custom Markdown directory path
python run_ingestion.py path/to/markdown/docs
```

> **Note**: This pipeline runs entirely in-memory and offline. No embeddings are calculated, no vector database calls (Qdrant) are performed, and no external LLM APIs are invoked.



---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- `pip` package manager

### 1. Create a Virtual Environment

Navigate to the `backend/` directory and create an isolated virtual environment:

```bash
cd backend
python3 -m venv .venv
```

Activate the virtual environment:

- **macOS / Linux:**
  ```bash
  source .venv/bin/activate
  ```
- **Windows (Command Prompt):**
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```

### 2. Install Dependencies

Install backend requirements:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Set your `EMBEDDING_API_KEY` and customized Qdrant endpoints in `.env` if connecting to live services.

### 4. (Optional) Run Local Qdrant for Development

To run a local Qdrant instance for development with Docker:

```bash
docker run -d -p 6333:6333 -p 6334:6334 -v $(pwd)/qdrant_storage:/qdrant/storage:z qdrant/qdrant
```

> **Note:** Running a live Qdrant server is **not** required for unit tests. All tests use mocks or in-memory instances.

---

## Running Tests

Run the complete unit test suite (including model validation, mock embedding tests, and vector store tests):

```bash
# Using pytest
pytest -v

# Or using standard library unittest
python -m unittest discover tests -v
```

---

## Running the Application

### Option A: Using Uvicorn (Development with Auto-reload)

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Option B: Running via Python Module

```bash
python -m app.main
```

The server will start at: `http://127.0.0.1:8000`

---

## API Endpoints

### 1. Health Check

Verifies server status without external dependencies.

- **URL:** `GET /health`
- **Response Format:** `application/json`
- **Example Response:**
  ```json
  {
    "status": "ok"
  }
  ```

**Verify using cURL:**
```bash
curl -X GET http://127.0.0.1:8000/health
```

### 2. Interactive Documentation

FastAPI provides built-in, interactive OpenAPI documentation:

- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI JSON:** [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## Current Scope & Future Roadmap

- **PR Scope:** Vector search foundation layer:
  - Settings configuration for embedding providers and Qdrant vector store.
  - `BaseEmbeddingService` and `OpenAIEmbeddingService` with text/batch/query embedding methods.
  - `BaseVectorStoreService` and `QdrantVectorStoreService` with collection management and chunk vector storage preserving citation provenance.
  - Mocked unit tests for embedding and vector store services.
- **Planned in Future PRs:**
  - Document ingestion & file parsers (`app/services/ingestion.py`)
  - Retrieval and search endpoints with hybrid filtering (`app/services/retrieval.py`)
  - Grounded answer generation and LLM response formatting (`app/services/generation.py`)
  - Query API endpoints (`/api/v1/query`, `/api/v1/retrieval`, `/api/v1/documents`)
