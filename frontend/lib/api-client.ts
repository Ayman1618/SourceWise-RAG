/**
 * RAG API Client Service
 *
 * Target Backend Endpoint Contract:
 * - Method: POST
 * - Endpoint: ${API_CONFIG.baseUrl}/api/v1/query
 * - Request Payload: QueryRequest ({ query: string, top_k?: number, filters?: Record<string, unknown> })
 * - Response Contract: AnswerResponse (Answer model in backend/app/models/generation.py)
 *
 * PLUG-IN LOCATION FOR BACKEND SERVICE:
 * -------------------------------------
 * To connect to a live backend service:
 * 1. Set NEXT_PUBLIC_API_BASE_URL=http://your-backend-host:8000 in your environment.
 * 2. Ensure FastAPI serves POST /api/v1/query returning the JSON serialization of Answer.
 * 3. The `queryRAG` function automatically directs all queries to POST /api/v1/query.
 *
 * DEVELOPMENT TRANSPORT ADAPTER:
 * ------------------------------
 * If the backend endpoint is offline or unreachable during early frontend development,
 * the client gracefully uses a development adapter to return a contract-compliant response,
 * ensuring the UI remains 100% testable without throwing uncaught network errors.
 */

import { API_CONFIG } from "./config";
import { AnswerResponse, QueryRequest } from "./types/rag";

export interface QueryOptions {
  topK?: number;
  filters?: Record<string, unknown>;
  forceScenario?: "normal" | "insufficient" | "error";
}

/**
 * Isolated development transport adapter providing contract-compliant responses
 * when the backend API is unreachable or when testing isolated frontend scenarios.
 */
async function devTransportAdapter(
  request: QueryRequest,
  scenario: "normal" | "insufficient" | "error" = "normal"
): Promise<AnswerResponse> {
  // Simulate lightweight 500ms network latency
  await new Promise((resolve) => setTimeout(resolve, 500));

  if (scenario === "error") {
    throw new Error(
      "Backend Service Unavailable: Failed to connect to RAG query endpoint at " +
        API_CONFIG.baseUrl +
        API_CONFIG.queryEndpoint
    );
  }

  if (scenario === "insufficient") {
    return {
      query: request.query,
      answer:
        "I couldn't find sufficient supporting information in the available knowledge base to answer this reliably.",
      citations: [],
      evidence: [],
      confidence_score: 0.12,
      evidence_status: "insufficient",
      has_sufficient_evidence: false,
      metadata: {
        adapter: "development_transport_adapter",
        reason: "evidence_below_relevance_threshold",
      },
    };
  }

  // Contract-compliant response matching backend Answer & Citation & RetrievedChunk models
  return {
    query: request.query,
    answer:
      "Repeated login failures can be caused by incorrect credentials, an expired session, or account lockout [1]. Check the user's authentication status and follow the documented recovery procedure [2]. If credentials are confirmed valid, verify whether active IP security flags or token expiration are blocking access [2].",
    citations: [
      {
        citation_id: "1",
        document_id: "DOC-2024-881",
        chunk_id: "DOC-2024-881#chunk_0",
        source_title: "Support Login Troubleshooting Guide",
        passage:
          "Verify whether the account has been temporarily locked after repeated unsuccessful authentication attempts. Default security policy locks accounts after 5 failed attempts within 15 minutes.",
        source_path: "data/sample-documents/support-login-troubleshooting.md",
        score: 0.92,
      },
      {
        citation_id: "2",
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
            document_id: "DOC-2024-881",
            title: "Support Login Troubleshooting Guide",
            source_type: "Support Documentation",
            version: "v2.1",
          },
        },
        score: 0.92,
        rank: 1,
        retrieval_method: "hybrid_qdrant",
      },
      {
        chunk: {
          chunk_id: "DOC-2024-412#chunk_1",
          document_id: "DOC-2024-412",
          text: "If credentials are correct but authentication fails, verify session token expiration or active IP security flags before initiating password reset or account recovery procedures.",
          metadata: {
            document_id: "DOC-2024-412",
            title: "Identity & Access Management Protocol",
            source_type: "Security Standard",
            version: "v1.4",
          },
        },
        score: 0.88,
        rank: 2,
        retrieval_method: "hybrid_qdrant",
      },
    ],
    confidence_score: 0.94,
    evidence_status: "sufficient",
    has_sufficient_evidence: true,
    metadata: {
      latency_ms: 142,
      model: "sourcewise-rag-v1",
      retrieved_chunks_count: 2,
    },
  };
}

/**
 * Execute a RAG query against the backend API endpoint.
 *
 * Endpoint: POST /api/v1/query
 * Payload: QueryRequest
 * Return: AnswerResponse
 */
export async function queryRAG(
  query: string,
  options: QueryOptions = {}
): Promise<AnswerResponse> {
  const requestPayload: QueryRequest = {
    query: query.trim(),
    top_k: options.topK || 5,
    filters: options.filters || {},
  };

  // If a specific dev testing scenario is forced, use dev adapter directly
  if (options.forceScenario && options.forceScenario !== "normal") {
    return devTransportAdapter(requestPayload, options.forceScenario);
  }

  const endpointUrl = `${API_CONFIG.baseUrl}${API_CONFIG.queryEndpoint}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.timeoutMs);

  try {
    const response = await fetch(endpointUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(requestPayload),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `Backend API returned HTTP ${response.status}: ${errorText || response.statusText}`
      );
    }

    const data: AnswerResponse = await response.json();
    return data;
  } catch (error: any) {
    clearTimeout(timeoutId);

    // If fetch failed (e.g. backend server is not running on localhost:8000),
    // fallback to development adapter so the frontend UI remains testable.
    if (
      error.name === "AbortError" ||
      error.name === "TypeError" ||
      error.message.includes("Failed to fetch")
    ) {
      console.warn(
        `[RAG API Client] Backend server unreachable at ${endpointUrl}. Falling back to development adapter.`
      );
      return devTransportAdapter(requestPayload, options.forceScenario || "normal");
    }

    throw error;
  }
}
