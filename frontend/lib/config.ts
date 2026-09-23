/**
 * Frontend Configuration for SourceWise RAG Integration.
 */

export const API_CONFIG = {
  /**
   * Base URL for the Backend FastAPI Service.
   * Configured via NEXT_PUBLIC_API_URL or NEXT_PUBLIC_API_BASE_URL.
   * Default fallback: http://localhost:8000
   */
  baseUrl:
    process.env.NEXT_PUBLIC_API_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "http://localhost:8000",

  /**
   * RAG Query Endpoint matching FastAPI route POST /api/v1/query
   */
  queryEndpoint: "/api/v1/query",

  /**
   * Timeout in milliseconds for backend RAG queries (15s)
   */
  timeoutMs: 15000,
};
