# SourceWise RAG — Backend Service

Backend service for SourceWise RAG, an evidence-first enterprise knowledge assistant designed to retrieve, verify, and cite internal documentation passages.

---

## Purpose

The backend provides the API infrastructure, data models, pipeline contracts, and services for SourceWise RAG:
- **Foundational Architecture:** FastAPI application setup, structured configuration via Pydantic Settings, modular router layout, and health checks.
- **RAG Pipeline Contracts:** Typed Pydantic data models establishing strict provenance and citation traceability between documents, chunks, retrieved evidence, citations, and generated answers.
- **Service Interfaces:** Abstract base class contracts for document ingestion, retrieval, and grounded answer generation.

> **Note:** Actual implementations of embedding generation, Qdrant vector indexing, hybrid search, and LLM answer generation will be incrementally introduced in subsequent PRs.

---

## Technology Stack

- **Runtime:** Python 3.10+ (Recommended: Python 3.12)
- **Web Framework:** [FastAPI](https://fastapi.tiangolo.com/) (0.110+)
- **ASGI Server:** [Uvicorn](https://www.uvicorn.org/) (0.28+)
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
│       ├── retrieval.py      # BaseRetrievalService abstract interface
│       └── generation.py     # BaseGenerationService abstract interface
├── tests/
│   ├── __init__.py           # Test suite package
│   ├── test_ingestion_chunking.py # Ingestion, chunking, overlap & boundary tests
│   ├── test_models.py        # Model validation and traceability tests
│   └── test_services.py      # Service contract and interface tests
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
RetrievedChunk (Ranked & scored candidate evidence)
   │
   ▼
Citation (Verifiable citation mapping passage → chunk_id → document_id)
   │
   ▼
Answer (Grounded answer payload delivered to the client)
```

### Why Traceability Matters

1. **Hallucination Prevention:** By enforcing explicit `document_id` and `chunk_id` linkages at the data model level, answers cannot cite ungrounded information.
2. **Auditability & Compliance:** Enterprise users can inspect the exact source passage and document metadata backing any claim.
3. **Graceful Refusal:** When insufficient evidence is retrieved, the pipeline signals `evidence_status = "refused"` or `"insufficient"`.

---

## Pipeline Service Interfaces

The backend defines abstract service contracts in `app/services/` to guide future implementations without coupling business logic to data models:

- **`BaseIngestionService`** (`ingest`, `chunk_document`): Normalizes raw sources into `Document` objects and chunks them into discrete `Chunk` instances.
- **`BaseRetrievalService`** (`retrieve`): Queries dense/sparse/hybrid vector indexes and returns ordered `RetrievedChunk` evidence lists.
- **`BaseGenerationService`** (`generate`): Synthesizes grounded `Answer` responses containing verified `Citation` references from retrieved evidence.

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

Default settings in `.env.example`:

```env
APP_ENV=development
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
```

---

## Running Tests

Run the model and service contract test suite:

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

- **PR Scope:** Foundation server, typed core RAG models (`Document`, `Chunk`, `RetrievedChunk`, `Citation`, `Answer`), and abstract pipeline interfaces (`BaseIngestionService`, `BaseRetrievalService`, `BaseGenerationService`).
- **Planned in Future PRs:**
  - Document ingestion & markdown/PDF parsers (`app/services/ingestion.py`)
  - Qdrant vector database integration & collection management
  - Embeddings generation & hybrid retrieval (`app/services/retrieval.py`)
  - OpenAI / LLM response generation with citation attribution (`app/services/generation.py`)
  - Query API endpoints (`/api/v1/query`, `/api/v1/retrieval`, `/api/v1/documents`)
