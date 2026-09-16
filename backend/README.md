# SourceWise RAG — Backend Service

Backend service for SourceWise RAG, an evidence-first enterprise knowledge assistant designed to retrieve, verify, and cite internal documentation passages.

---

## Purpose

The backend provides the API infrastructure and services for SourceWise RAG. In this foundational release (PR 4), the backend establishes the core FastAPI application setup, structured configuration management via Pydantic Settings, modular routing architecture, and a health-check endpoint.

> **Note:** Core RAG capabilities (document ingestion, chunking, embeddings, vector search with Qdrant, LLM generation, grounding verification, and citation mapping) will be incrementally introduced in subsequent PRs.

---

## Technology Stack

- **Runtime:** Python 3.10+ (Recommended: Python 3.12)
- **Web Framework:** [FastAPI](https://fastapi.tiangolo.com/) (0.110+)
- **ASGI Server:** [Uvicorn](https://www.uvicorn.org/) (0.28+)
- **Data Validation & Settings:** [Pydantic v2](https://docs.pydantic.dev/) & [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

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
│   └── models/
│       ├── __init__.py       # Data models package
│       └── health.py         # Health check response schemas
├── requirements.txt          # Minimal foundational Python dependencies
├── .env.example              # Example environment configuration
└── README.md                 # Backend documentation
```

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

Install the foundational backend requirements:

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

## Running the Application

### Option A: Using Uvicorn Directly (Recommended for Development)

Run with auto-reload enabled:

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

## Current Limitations & Roadmap

- **PR 4 Foundation Scope:** This release establishes only the backend web server, settings manager, and health verification endpoint.
- **Planned in Future PRs:**
  - Ingestion pipeline (`/api/v1/documents`)
  - Retrieval & hybrid search (`/api/v1/retrieval`)
  - Grounded RAG query answering (`/api/v1/query`)
  - Vector database integration (Qdrant)
  - Embedding generation & OpenAI-compatible LLM orchestration
  - Hallucination guardrails, refusal policy, and citation verification
