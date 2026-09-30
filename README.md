# SourceWise RAG

> Retrieve. Ground. Verify.

An enterprise knowledge assistant that retrieves, verifies, and cites trustworthy information from internal documentation.

## Problem

Enterprise knowledge is scattered across documentation, wikis, and support tickets, making it difficult to find exact, trustworthy passages. This leads to inconsistent support answers, slow resolution times, and AI hallucinations.

## What It Does

SourceWise RAG combines semantic retrieval with grounded generation to answer questions strictly using retrieved internal evidence. Every factual statement is backed by verifiable citations mapped to source passages, and the system refuses to answer when sufficient evidence is unavailable.

## Core Pipeline

Ingest → Chunk → Embed → Index → Retrieve → Generate → Cite

## Tech Stack & Architecture

SourceWise RAG is built for zero mandatory API spending for development and demo usage:
- **Embeddings:** Google Gemini (`gemini-embedding-2`, 1536 dimensions) via Google GenAI free tier
- **Generation:** Google Gemini (`gemini-2.5-flash-lite`) for grounded answer synthesis & structured citations
- **Vector Database:** [Qdrant](https://qdrant.tech/) for dense vector similarity search with metadata filtering
- **Backend:** Python 3.12, FastAPI, Pydantic v2
- **Frontend:** Next.js, React, TypeScript


## Project Structure

- `backend/` — Python backend, document ingestion, RAG services, retrieval logic, Dockerfile, and API endpoints.
- `frontend/` — Next.js and TypeScript web application.
- `data/sample-documents/` — Non-sensitive sample documents for local development and testing.
- `evaluation/` — Retrieval, grounding, citation, refusal, and evaluation resources.
- `docs/` — Architecture documentation, technical decisions, and [Deployment Guide](docs/deployment.md).

## Deployment & Production Readiness

SourceWise RAG is fully containerized and production-ready for zero-cost demo deployment on free-tier platforms:
- **Zero Paid Dependencies**: Powered by Google Gemini free tier (`gemini-2.5-flash-lite`, `gemini-embedding-2`) + Qdrant Cloud free tier (1GB cluster).
- **Backend Container**: Production-grade `Dockerfile` listening on `0.0.0.0` with dynamic `$PORT` support.
- **Frontend Configuration**: Environment-driven `NEXT_PUBLIC_API_BASE_URL` without hardcoded URLs.
- **Health Probes**: Isolated liveness probe (`GET /health`) and database readiness probe (`GET /health/ready`).
- **Smoke Testing**: Built-in verification script (`python scripts/smoke_test.py --base-url <url>`).

For complete step-by-step instructions, see the **[Production Deployment Guide](docs/deployment.md)**.

## Team

- **Ayman Velani** — RAG Architecture & Backend  
  Responsible for the RAG pipeline, LLM integration, embeddings, retrieval strategy, grounding/guardrails, and backend architecture.

- **Yash Bodhe** — Data Engineering & Document Pipeline  
  Responsible for document ingestion, text extraction, chunking, metadata enrichment, embeddings, and vector indexing.

- **Om Bankar** — Frontend & Application Integration  
  Responsible for the Next.js interface, chat experience, citation rendering, API integration, document upload flow, and frontend testing.
