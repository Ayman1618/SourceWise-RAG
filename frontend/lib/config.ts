/**
 * Frontend Configuration for SourceWise RAG Backend Integration.
 */

export const API_CONFIG = {
  /**
   * Base URL for Backend FastAPI RAG Service.
   * Environment variable: NEXT_PUBLIC_API_BASE_URL (or NEXT_PUBLIC_API_URL)
   * Default fallback: http://localhost:8000
   */
  baseUrl:
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://localhost:8000",

  /**
   * RAG Query Endpoint Path (POST /api/v1/query)
   */
  queryEndpoint: "/api/v1/query",

  /**
   * Timeout in milliseconds for backend query requests (15 seconds)
   */
  timeoutMs: 15000,
};
