# SourceWise RAG — Backend Production Deployment Guide

This guide describes how to deploy the SourceWise RAG FastAPI backend to any free-tier container hosting platform (e.g., Render, Railway, Fly.io, Hugging Face Spaces, Koyeb, Cloud Run) with zero mandatory API spending.

---

## Target Deployment Architecture

```
┌────────────────────────────────────────┐
│ Deployed Frontend (Next.js / Vercel)   │
└───────────────────┬────────────────────┘
                    │ HTTPS requests
                    ▼
┌────────────────────────────────────────┐
│ FastAPI Backend (Container / Docker)   │
│  - GET  /health (Liveness)             │
│  - GET  /health/ready (Readiness)      │
│  - POST /api/v1/query (Grounded RAG)   │
└──────────────┬──────────────────┬──────┘
               │                  │
               ▼                  ▼
┌───────────────────────┐  ┌──────────────────────────────────┐
│ Google Gemini API     │  │ Qdrant Cloud Vector Database     │
│ (Free Tier API Key)   │  │ (Free 1GB Cluster / Cloud Instance)│
│ - gemini-embedding-2  │  │ - 1536 Cosine Similarity Vectors │
│ - gemini-2.5-flash-lite│ └──────────────────────────────────┘
└───────────────────────┘
```

---

## Step 1: Set Up Free-Tier External Dependencies

1. **Google Gemini Free-Tier Key**:
   - Visit [Google AI Studio](https://aistudio.google.com/) and generate a free API key.
   - Used for embeddings (`gemini-embedding-2`) and generation (`gemini-2.5-flash-lite`).

2. **Qdrant Free-Tier Cluster**:
   - Register at [Qdrant Cloud](https://cloud.qdrant.io/) and create a free 1GB cluster.
   - Note your cluster URL (`https://<cluster-id>.<region>.cloud.qdrant.io:6333`) and API Key.

---

## Step 2: Deploy Backend to Container Platform

### Step 2.1: Create Web Service
1. Connect your GitHub repository to your container hosting provider (e.g. Render, Railway, Fly.io, Koyeb).
2. Select **Docker** deployment mode.
3. Set the **Root Directory** to `backend` and Dockerfile path to `Dockerfile` (or `backend/Dockerfile` if building from repository root).

### Step 2.2: Configure Environment Variables

Set the following environment variables in the platform dashboard (placeholders shown):

| Environment Variable | Recommended Value | Description |
|---|---|---|
| `APP_ENV` | `production` | Enables production mode and logging |
| `BACKEND_HOST` | `0.0.0.0` | Bind address for container |
| `PORT` | `8000` | (Or automatically injected by the platform) |
| `CORS_ORIGINS` | `https://your-frontend.vercel.app,http://localhost:3000` | Allowed frontend origin domains |
| `GEMINI_API_KEY` | `<your-free-tier-gemini-key>` | Google AI Studio free-tier API key |
| `GEMINI_GENERATION_MODEL` | `gemini-2.5-flash-lite` | Generation model |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-2` | Embedding model |
| `GEMINI_EMBEDDING_DIMENSION` | `1536` | Output embedding dimension size |
| `QDRANT_URL` | `https://<cluster-id>.cloud.qdrant.io:6333` | Qdrant endpoint URL |
| `QDRANT_API_KEY` | `<your-qdrant-api-key>` | Qdrant cluster access key |
| `QDRANT_COLLECTION_NAME` | `sourcewise_documents` | Target collection name |
| `QDRANT_VECTOR_SIZE` | `1536` | Vector size matching embedding model |
| `QDRANT_DISTANCE` | `Cosine` | Distance metric |

> **Security Note**: Never commit API keys or secret tokens to git.

---

## Step 3: Verify Deployment Endpoints

Once deployed and running, verify service health using cURL:

### 1. Liveness Check (No dependency checks)
```bash
curl -X GET https://<your-backend-domain>/health
```
**Expected Response (HTTP 200)**:
```json
{
  "status": "ok"
}
```

### 2. Readiness Check (Verifies vector store connectivity)
```bash
curl -X GET https://<your-backend-domain>/health/ready
```
**Expected Response (HTTP 200)**:
```json
{
  "status": "ready",
  "database": "connected",
  "details": {
    "collection_checked": true,
    "collection_exists": true
  }
}
```

---

## Step 4: Index Initial Documents (Explicit CLI Operation)

Document indexing is decoupled from server startup to ensure containers boot instantly.

To index documentation into your production vector store, run the CLI tool locally with production Qdrant and Gemini credentials:

```bash
# In backend/ directory:
GEMINI_API_KEY=<your-key> \
QDRANT_URL=https://<cluster-id>.cloud.qdrant.io:6333 \
QDRANT_API_KEY=<your-qdrant-key> \
python -m app.cli.index ../data/sample-documents
```

---

## Step 5: Configure Frontend Web Application

In your frontend deployment (e.g. Vercel / Netlify):

1. Set the environment variable:
   ```env
   NEXT_PUBLIC_API_URL=https://<your-backend-domain>
   ```
2. Redeploy frontend.
3. Test end-to-end question answering and verified citation rendering.
