# SourceWise RAG — Production Deployment & Integration Guide

This guide describes how to deploy the full SourceWise RAG application (FastAPI backend + Next.js frontend) to free-tier cloud infrastructure with zero mandatory API spending.

---

## Target Deployment Architecture

```
┌────────────────────────────────────────┐
│ Deployed Next.js Frontend (e.g. Vercel)│
│  - Configured with                     │
│    NEXT_PUBLIC_API_BASE_URL            │
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
│ (Free-Tier API Key)   │  │ (Free 1GB Cluster / Cloud Instance)│
│ - gemini-embedding-2  │  │ - 1536 Cosine Similarity Vectors │
│ - gemini-2.5-flash-lite│ └──────────────────────────────────┘
└───────────────────────┘
```

> **Note on Free-Tier Usage**: Free tiers offered by Google Gemini (e.g., rate-limited requests per minute) and Qdrant Cloud (1GB free cluster) provide ample capacity for demos and testing, but are subject to provider terms and rate limits. The architecture is intentionally designed with zero paid service dependencies.

---

## Complete 10-Step Deployment Flow

### Step 1: Create Free-Tier Qdrant Instance
1. Register for an account at [Qdrant Cloud Console](https://cloud.qdrant.io/).
2. Create a free 1GB cluster.
3. Note your cluster URL (e.g. `https://<cluster-id>.<region>.cloud.qdrant.io:6333`) and generate an API key.

### Step 2: Obtain Gemini Free-Tier API Key
1. Visit [Google AI Studio](https://aistudio.google.com/).
2. Create a new project and generate a free Gemini API key.
3. This key powers both vector embeddings (`gemini-embedding-2`) and grounded generation (`gemini-2.5-flash-lite`).

### Step 3: Deploy Backend Container
Deploy the backend using any container platform (e.g. Render, Railway, Fly.io, Koyeb, Hugging Face Spaces):
1. Create a new **Web Service** connected to your GitHub repository.
2. Select **Docker** deployment.
3. Set **Root Directory** to `backend` and use `Dockerfile` (or root `backend/Dockerfile`).

### Step 4: Configure Backend Environment Variables
Set the following environment variables in your backend service dashboard:

| Variable | Example / Recommended Value | Description |
|---|---|---|
| `APP_ENV` | `production` | Enables production mode and logging |
| `BACKEND_HOST` | `0.0.0.0` | Host binding inside container |
| `PORT` | `8000` | Platform port override (injected by host) |
| `CORS_ORIGINS` | `https://your-frontend.vercel.app` | Allowed frontend origin(s) |
| `GEMINI_API_KEY` | `your_gemini_api_key_here` | Google AI Studio free API key |
| `GEMINI_GENERATION_MODEL` | `gemini-2.5-flash-lite` | Generation model |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-2` | Embedding model (1536 dimensions) |
| `GEMINI_EMBEDDING_DIMENSION` | `1536` | Vector size matching Qdrant |
| `QDRANT_URL` | `https://<cluster-id>.cloud.qdrant.io:6333` | Qdrant Cloud cluster endpoint |
| `QDRANT_API_KEY` | `your_qdrant_api_key_here` | Qdrant access token |
| `QDRANT_COLLECTION_NAME` | `sourcewise_documents` | Target collection name |
| `QDRANT_VECTOR_SIZE` | `1536` | Vector size |
| `QDRANT_DISTANCE` | `Cosine` | Similarity distance |

> **Security Note**: Never commit API keys or production tokens to git.

### Step 5: Deploy Frontend Web Application
1. Connect your repository to a frontend hosting platform (e.g., [Vercel](https://vercel.com/) or Netlify).
2. Set the root directory to `frontend`.
3. Build command: `npm run build`, Output directory: `.next`.

### Step 6: Set `NEXT_PUBLIC_API_BASE_URL` in Frontend
1. In your frontend hosting dashboard settings (Environment Variables), set:
   ```env
   NEXT_PUBLIC_API_BASE_URL=https://<your-deployed-backend-domain>
   ```
2. Trigger a redeploy so the build picks up the production backend URL.

### Step 7: Verify Liveness (`GET /health`)
Verify that the FastAPI service is running and responsive:
```bash
curl -i -X GET https://<your-backend-domain>/health
```
**Expected Response (HTTP 200 OK)**:
```json
{
  "status": "ok"
}
```

### Step 8: Verify Readiness (`GET /health/ready`)
Verify that the backend has established a working connection to Qdrant Cloud:
```bash
curl -i -X GET https://<your-backend-domain>/health/ready
```
**Expected Response (HTTP 200 OK)**:
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

### Step 9: Index Knowledge Base Documents
Document indexing is decoupled from application startup to allow instantaneous container boots and zero-downtime updates.

#### 1. Dry-Run Verification (Preview parsing without API/DB calls)
```bash
python backend/run_indexing.py --dry-run
```

#### 2. Production Indexing (Live Gemini Embedding + Qdrant Cloud)
Run the production indexing tool with configured credentials:
```bash
cd backend
source .venv/bin/activate

# Read from .env or supply explicitly:
GEMINI_API_KEY="your_gemini_api_key_here" \
QDRANT_URL="https://<cluster-id>.cloud.qdrant.io:6333" \
QDRANT_API_KEY="your_qdrant_api_key_here" \
python run_indexing.py ../data/sample-documents
```

**Expected Output:**
```text
Discovering documents in: /path/to/data/sample-documents
Discovered and parsed 3 document(s):
  - [sample-api-rate-limits] 'API Rate Limits and Quota Management'
  - [sample-authentication-guide] 'Product Authentication Guide'
  - [sample-login-troubleshooting] 'Support Login Troubleshooting Guide'
Chunked documents into 10 chunk(s).
Generating dense embeddings using Gemini (gemini-embedding-2)...
Upserting vector points into Qdrant collection 'sourcewise_documents'...

--- Indexing Summary ---
Documents processed:  3
Chunks created:       10
Embeddings generated: 10
Vectors indexed:      10
Failures:             0
```

#### 3. Verify Indexed Data in Qdrant
Verify that vector points are present in the collection:
```bash
curl -X POST https://<cluster-id>.cloud.qdrant.io:6333/collections/sourcewise_documents/points/count \
  -H "api-key: <your-qdrant-key>" \
  -H "Content-Type: application/json" \
  -d '{"exact": true}'
```

### Step 10: Run an End-to-End Query
Test end-to-end question answering and verified citation rendering against your indexed knowledge base:
```bash
curl -X POST https://<your-backend-domain>/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I troubleshoot login failures?",
    "top_k": 3
  }'
```
Or open your deployed frontend application in your browser and submit a query through the Ask interface!

---

## Automated Deployment Smoke Test

SourceWise RAG includes a standalone deployment verification script:

```bash
python scripts/smoke_test.py --base-url https://<your-backend-domain> --frontend-url https://<your-frontend-domain>
```

The script performs an automated check of:
1. Backend connectivity & liveness (`/health`)
2. Vector database readiness (`/health/ready`)
3. Query API response schema, citations, and evidence status (`/api/v1/query`)
4. Frontend environment contract alignment

---

## Security Best Practices
- **No Hardcoded Secrets**: Secrets and credentials must only be injected via environment variables.
- **Restricted Production CORS**: Configure `CORS_ORIGINS` to specify only trusted frontend domains. Avoid universal wildcards (`*`) in production.
- **Error Detail Masking**: Internal server errors (HTTP 500) automatically mask stack traces and database credentials from client responses.
- **Automated Secret Scan**: Run `python scripts/security_check.py` prior to publishing or committing changes.
- **Security Policy & Checklist**: For comprehensive environment variable classifications, public vs secret guidelines, and rotation procedures, consult the **[Security Policy](security.md)**.

