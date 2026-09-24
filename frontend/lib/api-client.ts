/**
 * RAG API Client Service
 *
 * Target Backend Endpoint Contract:
 * - Method: POST
 * - Endpoint: ${API_CONFIG.baseUrl}/api/v1/query
 * - Request Payload: { query: string, top_k?: number, filters?: Record<string, unknown> }
 * - Response Contract: AnswerResponse (Answer model in backend/app/models/generation.py)
 */

import { API_CONFIG } from "./config";
import { AnswerResponse, QueryRequest } from "./types/rag";

export class RAGApiError extends Error {
  public type: "network_error" | "backend_error" | "timeout_error" | "validation_error";
  public statusCode?: number;

  constructor(
    message: string,
    type: "network_error" | "backend_error" | "timeout_error" | "validation_error",
    statusCode?: number
  ) {
    super(message);
    this.name = "RAGApiError";
    this.type = type;
    this.statusCode = statusCode;
  }
}

export interface QueryOptions {
  topK?: number;
  filters?: Record<string, unknown>;
  testMode?: boolean;
  scenario?: "normal" | "insufficient" | "refused" | "error";
}

/**
 * Isolated dev test helper used ONLY when testMode option is explicitly enabled during test execution.
 */
function getTestMockResponse(
  query: string,
  scenario: "normal" | "insufficient" | "refused" | "error" = "normal"
): AnswerResponse {
  if (scenario === "error") {
    throw new RAGApiError("Simulated backend server error for testing", "backend_error", 500);
  }

  if (scenario === "refused") {
    return {
      query,
      answer:
        "I couldn't find sufficient supporting information in the available knowledge base to answer this reliably.",
      citations: [],
      evidence: [],
      confidence_score: 0.0,
      evidence_status: "refused",
      has_sufficient_evidence: false,
      metadata: { source: "test_mode" },
    };
  }

  if (scenario === "insufficient") {
    return {
      query,
      answer:
        "I couldn't find sufficient supporting information in the available knowledge base to answer this reliably.",
      citations: [],
      evidence: [],
      confidence_score: 0.0,
      evidence_status: "insufficient",
      has_sufficient_evidence: false,
      metadata: { source: "test_mode" },
    };
  }

  return {
    query,
    answer:
      "Repeated login failures can be caused by incorrect credentials, an expired session, or account lockout [1]. Check the user's authentication status and follow the documented recovery procedure [2]. If credentials are confirmed valid, verify whether active IP security flags or token expiration are blocking access [2].",
    citations: [
      {
        citation_id: "cite_1",
        document_id: "DOC-2024-881",
        chunk_id: "DOC-2024-881#chunk_0",
        source_title: "Support Login Troubleshooting Guide",
        passage:
          "Verify whether the account has been temporarily locked after repeated unsuccessful authentication attempts. Default security policy locks accounts after 5 failed attempts within 15 minutes.",
        source_path: "data/sample-documents/support-login-troubleshooting.md",
        score: 0.92,
      },
      {
        citation_id: "cite_2",
        document_id: "DOC-2024-412",
        chunk_id: "DOC-2024-412#chunk_1",
        source_title: "Identity & Access Management Protocol",
        passage:
          "If credentials are correct but authentication fails, verify session token expiration or active IP security flags before initiating password reset or account recovery procedures.",
        source_path: "data/sample-documents/product-authentication-guide.md",
        score: 0.88,
      },
    ],
    evidence: [
      {
        chunk: {
          chunk_id: "DOC-2024-881#chunk_0",
          document_id: "DOC-2024-881",
          text: "Verify whether the account has been temporarily locked after repeated unsuccessful authentication attempts. Default security policy locks accounts after 5 failed attempts within 15 minutes.",
          metadata: {
            title: "Support Login Troubleshooting Guide",
            source_type: "Support Documentation",
            version: "v2.1",
          },
        },
        score: 0.92,
        rank: 1,
        retrieval_method: "hybrid",
      },
      {
        chunk: {
          chunk_id: "DOC-2024-412#chunk_1",
          document_id: "DOC-2024-412",
          text: "If credentials are correct but authentication fails, verify session token expiration or active IP security flags before initiating password reset or account recovery procedures.",
          metadata: {
            title: "Identity & Access Management Protocol",
            source_type: "Security Standard",
            version: "v1.4",
          },
        },
        score: 0.88,
        rank: 2,
        retrieval_method: "hybrid",
      },
    ],
    confidence_score: 0.94,
    evidence_status: "sufficient",
    has_sufficient_evidence: true,
    metadata: { source: "test_mode" },
  };
}

/**
 * Execute a RAG query against the backend API endpoint (POST /api/v1/query).
 */
export async function queryRAG(
  queryText: string,
  options: QueryOptions = {}
): Promise<AnswerResponse> {
  const trimmed = queryText.trim();
  if (!trimmed) {
    throw new RAGApiError(
      "Query cannot be empty or whitespace only",
      "validation_error"
    );
  }

  // Explicit testMode override for unit test suites
  if (options.testMode) {
    await new Promise((res) => setTimeout(res, 200));
    return getTestMockResponse(trimmed, options.scenario);
  }

  const endpointUrl = `${API_CONFIG.baseUrl}${API_CONFIG.queryEndpoint}`;
  const payload: QueryRequest = {
    query: trimmed,
    top_k: options.topK || 5,
    filters: options.filters || null,
  };

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.timeoutMs);

  try {
    const response = await fetch(endpointUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorDetail = "";
      try {
        const errorJson = await response.json();
        errorDetail = errorJson.detail || errorJson.message || "";
      } catch {
        errorDetail = await response.text();
      }

      throw new RAGApiError(
        errorDetail || `Backend API returned status HTTP ${response.status}`,
        "backend_error",
        response.status
      );
    }

    const data: AnswerResponse = await response.json();
    return data;
  } catch (error: any) {
    clearTimeout(timeoutId);

    if (error instanceof RAGApiError) {
      throw error;
    }

    if (error.name === "AbortError") {
      throw new RAGApiError(
        "Request timed out. The backend RAG service took too long to respond.",
        "timeout_error"
      );
    }

    // Network / connection refused / offline server error
    throw new RAGApiError(
      `Network Error: Unable to connect to backend RAG API at ${endpointUrl}. Please ensure the backend server is running.`,
      "network_error"
    );
  }
}
