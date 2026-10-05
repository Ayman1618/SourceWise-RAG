# SourceWise RAG — Repository Security & Secrets Policy

This document defines the security architecture, environment variable classifications, credential protection guidelines, and release hardening policies for SourceWise RAG.

---

## 1. Core Security Principles

1. **Zero Hardcoded Credentials**: API keys, database tokens, passwords, and private certificates must **never** be hardcoded in source code, committed to git, or baked into container images.
2. **Strict Public vs. Secret Boundary**: Browser-facing client applications only receive non-sensitive endpoints (`NEXT_PUBLIC_API_BASE_URL`). Private AI and database credentials stay exclusively in the backend runtime.
3. **Automated Secret Scanning**: Pre-commit and CI scans (`python scripts/security_check.py`) automatically detect and reject credential patterns before code can be published.
4. **Error Sanitization & Masking**: Production errors mask connection strings, stack traces, and internal authorization headers to prevent info leakage.

---

## 2. Environment Variables: Public vs. Secret Classification

| Variable | Classification | Scope | Description | Safe for Browser? |
|---|---|---|---|---|
| `GEMINI_API_KEY` | **SECRET** | Backend Runtime | Google AI Studio API key for embeddings and generation | **NO** (Never expose) |
| `QDRANT_API_KEY` | **SECRET** | Backend Runtime | API key for authenticated Qdrant Cloud cluster | **NO** (Never expose) |
| `QDRANT_URL` | **CONFIG** | Backend Runtime | Qdrant vector database URL (e.g. `http://localhost:6333`) | **NO** |
| `NEXT_PUBLIC_API_BASE_URL` | **PUBLIC** | Frontend Client | Public URL of backend FastAPI service for browser fetch calls | **YES** (Public endpoint) |
| `NEXT_PUBLIC_API_URL` | **PUBLIC** | Frontend Client | Backward-compatible alias for frontend backend URL | **YES** (Public endpoint) |
| `CORS_ORIGINS` | **CONFIG** | Backend Runtime | Comma-separated list of allowed frontend origins | **NO** |
| `APP_ENV` | **CONFIG** | Backend Runtime | Application environment (`development`, `production`, `test`) | **NO** |
| `BACKEND_HOST` | **CONFIG** | Backend Runtime | Host interface binding (default `0.0.0.0`) | **NO** |
| `BACKEND_PORT` / `PORT` | **CONFIG** | Backend Runtime | Listening port (default `8000`) | **NO** |
| `GEMINI_GENERATION_MODEL` | **CONFIG** | Backend Runtime | Generation model identifier (`gemini-2.5-flash-lite`) | **NO** |
| `GEMINI_EMBEDDING_MODEL` | **CONFIG** | Backend Runtime | Embedding model identifier (`gemini-embedding-2`) | **NO** |
| `GEMINI_EMBEDDING_DIMENSION`| **CONFIG** | Backend Runtime | Vector dimension size (`1536`) | **NO** |
| `QDRANT_COLLECTION_NAME` | **CONFIG** | Backend Runtime | Qdrant vector collection name | **NO** |
| `QDRANT_VECTOR_SIZE` | **CONFIG** | Backend Runtime | Dimensionality of collection points (`1536`) | **NO** |
| `QDRANT_DISTANCE` | **CONFIG** | Backend Runtime | Distance metric (`Cosine`) | **NO** |

> **Critical Rule on `NEXT_PUBLIC_*` Variables**:  
> In Next.js, all environment variables prefixed with `NEXT_PUBLIC_` are inlined directly into client JavaScript bundles sent to the user's browser. **NEVER** prefix API keys, service tokens, or private database credentials with `NEXT_PUBLIC_`.

---

## 3. How to Configure Secrets Locally

1. **Backend Environment Configuration**:
   ```bash
   cd backend
   cp .env.example .env
   ```
   Open `.env` and fill in your real credentials:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   QDRANT_URL=http://localhost:6333
   QDRANT_API_KEY=your_actual_qdrant_api_key_here  # Optional for local unauthenticated Qdrant
   ```

2. **Frontend Environment Configuration**:
   ```bash
   cd frontend
   cp .env.example .env.local
   ```
   Open `.env.local` and set the backend endpoint:
   ```env
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
   ```

3. **Verify Git Status**:
   Always verify that `.env` or `.env.local` are not tracked:
   ```bash
   git status
   ```
   Both `.env` and `.env.local` are ignored by root and frontend `.gitignore` rules.

---

## 4. How to Configure Deployment Secrets

### 4.1 Cloud Platforms (Render, Railway, Fly.io, Cloud Run)
Inject environment variables directly via the hosting dashboard or platform CLI:
- Navigate to your service's **Environment / Variables** settings.
- Add `GEMINI_API_KEY`, `QDRANT_URL`, and `QDRANT_API_KEY` as encrypted secrets.
- Set `APP_ENV=production`.
- Restrict `CORS_ORIGINS` to your production frontend domain (e.g. `https://your-app.vercel.app`).

### 4.2 Frontend Deployment (Vercel, Netlify)
- In the frontend project dashboard, add `NEXT_PUBLIC_API_BASE_URL=https://your-backend-api.onrender.com`.
- **Do not** add backend credentials to the frontend hosting platform.

### 4.3 Container / Docker Best Practices
- **No Baked Secrets**: The `Dockerfile` does not include `COPY .env` or `ENV GEMINI_API_KEY=...`.
- Secrets are supplied at container execution time:
  ```bash
  docker run -d \
    --name sourcewise-rag-backend \
    -p 8000:8000 \
    -e GEMINI_API_KEY="your_gemini_api_key_here" \
    -e QDRANT_URL="https://your-cluster.cloud.qdrant.io:6333" \
    -e QDRANT_API_KEY="your_qdrant_api_key_here" \
    sourcewise-rag-backend
  ```

---

## 5. What Must NEVER Be Committed

The following files and patterns are blocked by `.gitignore`, `.dockerignore`, and our automated scanner:

- `*.env`, `*.env.local`, `*.env.production`, `*.env.development` (Only `.env.example` with dummy values is allowed).
- Private key files: `*.pem`, `*.key`, `*.p12`, `*.pfx`, `id_rsa`, `id_ed25519`.
- Cloud credentials & service accounts: `*service-account*.json`, `*credentials*.json`.
- Live API keys or tokens in code, tests, documentation, sample data, or git commit messages.
- Connection strings containing embedded credentials or passwords (e.g. `scheme://username:password@host/database`).

---

## 6. Automated Secret Scanner

The repository includes a standalone automated security scanner:

```bash
python scripts/security_check.py
```

### Features:
- Scans all tracked repository files without requiring external network services or third-party packages.
- Detects high-risk patterns: Gemini API keys, OpenAI keys, AWS keys, GitHub tokens, webhook URLs, and private key blocks.
- Validates that no forbidden `.env` or credential files are tracked by git.
- Automatically masks detected values so output never leaks raw credentials into console logs.
- Returns exit code `0` on clean scans and exit code `1` on any detected violations.

---

## 7. Secret Rotation & Incident Response

If an API key or secret token is ever suspected of having been exposed:

1. **Immediate Revocation**:
   - For Google Gemini: Revoke the key in the [Google AI Studio Console](https://aistudio.google.com/).
   - For Qdrant Cloud: Invalidate the token in the [Qdrant Cloud Console](https://cloud.qdrant.io/).
2. **Re-issuance**:
   - Generate a new key and update your hosting provider's environment variables.
3. **Repository History Audit**:
   - If a secret was committed in git history, simply deleting it in a subsequent commit is **insufficient**. The credential must be rotated immediately, and repository history must be scrubbed using tools such as `git-filter-repo` or BFG Repo-Cleaner before public push.
