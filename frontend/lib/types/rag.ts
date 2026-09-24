/**
 * Frontend RAG Types matching the Backend Pydantic Contract
 *
 * Source of Truth:
 * - backend/app/models/query.py (QueryRequest)
 * - backend/app/models/generation.py (Answer, EvidenceStatus)
 * - backend/app/models/citation.py (Citation)
 * - backend/app/models/retrieval.py (RetrievedChunk)
 */

export type EvidenceStatus = "sufficient" | "insufficient" | "refused" | "unverified";

export interface QueryRequest {
  query: string;
  top_k?: number;
  filters?: Record<string, unknown> | null;
}

export interface Citation {
  citation_id: string;
  document_id: string;
  chunk_id: string;
  source_title: string;
  passage: string;
  source_path?: string | null;
  score?: number | null;
}

export interface ChunkMetadata {
  document_id?: string;
  title?: string;
  source_type?: string;
  version?: string;
  source_path?: string;
  filepath?: string;
  [key: string]: unknown;
}

export interface Chunk {
  chunk_id: string;
  document_id: string;
  text: string;
  metadata?: ChunkMetadata;
}

export interface RetrievedChunk {
  chunk: Chunk;
  score: number;
  rank: number;
  retrieval_method?: string | null;
}

export interface AnswerResponse {
  query: string;
  answer: string;
  citations: Citation[];
  evidence: RetrievedChunk[];
  confidence_score?: number | null;
  evidence_status: EvidenceStatus;
  has_sufficient_evidence: boolean;
  metadata?: Record<string, unknown>;
}

export type AskUIState = "idle" | "submitting" | "success" | "insufficient" | "refused" | "error";
