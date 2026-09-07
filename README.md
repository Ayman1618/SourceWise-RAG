# SourceWise RAG

> Retrieve. Ground. Verify.

An enterprise knowledge assistant that retrieves, verifies, and cites trustworthy information from internal documentation.

## Problem

Enterprise knowledge is scattered across documentation, wikis, and support tickets, making it difficult to find exact, trustworthy passages. This leads to inconsistent support answers, slow resolution times, and AI hallucinations.

## What It Does

SourceWise RAG combines semantic retrieval with grounded generation to answer questions strictly using retrieved internal evidence. Every factual statement is backed by verifiable citations mapped to source passages, and the system refuses to answer when sufficient evidence is unavailable.

## Core Pipeline

Ingest → Chunk → Embed → Index → Retrieve → Generate → Cite

## Tech Stack

- Python / TypeScript
- OpenAI-compatible API
- Embeddings
- Qdrant
- RAG
- Next.js

## Team

- **Ayman Velani** — RAG Architecture & Backend  
  Responsible for the RAG pipeline, LLM integration, embeddings, retrieval strategy, grounding/guardrails, and backend architecture.

- **Yash Bodhe** — Data Engineering & Document Pipeline  
  Responsible for document ingestion, text extraction, chunking, metadata enrichment, embeddings, and vector indexing.

- **Om Bankar** — Frontend & Application Integration  
  Responsible for the Next.js interface, chat experience, citation rendering, API integration, document upload flow, and frontend testing.
