/**
 * Frontend Configuration for Backend RAG Service Integration.
 */

export const API_CONFIG = {
  /**
   * Base URL for the backend API service.
   * Can be configured via NEXT_PUBLIC_API_BASE_URL environment variable.
   * Default fallback: http://localhost:8000
   */
  baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",

  /**
   * Primary RAG Query Endpoint Path matching backend FastAPI router contract.
   * Target endpoint: POST /api/v1/query
   */
  queryEndpoint: "/api/v1/query",

  /**
   * Request timeout in milliseconds (15 seconds).
   */
  timeoutMs: 15000,
};
