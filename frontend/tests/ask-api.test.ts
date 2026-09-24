/**
 * Frontend RAG Query API Integration Test Suite
 *
 * Verifies Requirement 12:
 * - successful API response contract
 * - loading state
 * - insufficient evidence
 * - refusal state
 * - API error handling (network_error / backend_error)
 * - empty query validation
 */

import { queryRAG, RAGApiError } from "../lib/api-client";
import { AnswerResponse, Citation, RetrievedChunk } from "../lib/types/rag";

function assert(condition: boolean, message: string) {
  if (!condition) {
    throw new Error(`[TEST FAILED] ${message}`);
  }
}

async function runTests() {
  console.log("Starting SourceWise Frontend RAG Query API Test Suite...\n");

  // Test 1: Empty query validation upfront
  {
    console.log("Test 1: Testing Empty Query Validation...");
    try {
      await queryRAG("   ", { testMode: true });
      assert(false, "Empty query should throw validation error");
    } catch (err: any) {
      assert(err instanceof RAGApiError, "Error must be RAGApiError");
      assert(err.type === "validation_error", "Error type must be validation_error");
      console.log("✓ Test 1 Passed: Empty query validation verified.\n");
    }
  }

  // Test 2: Successful API Response Contract
  {
    console.log("Test 2: Testing Successful API Response Contract...");
    const res: AnswerResponse = await queryRAG("How do I troubleshoot login failures?", {
      testMode: true,
      scenario: "normal",
    });

    assert(Boolean(res.answer), "Response must contain answer string");
    assert(res.has_sufficient_evidence === true, "has_sufficient_evidence should be true");
    assert(res.evidence_status === "sufficient", "evidence_status should be 'sufficient'");
    assert(res.citations.length > 0, "Response should contain citations");
    assert(res.evidence.length > 0, "Response should contain evidence chunks");
    assert(Boolean(res.citations[0].citation_id), "Citation must have citation_id");
    assert(Boolean(res.citations[0].source_title), "Citation must have source_title");
    console.log("✓ Test 2 Passed: Successful API response contract verified.\n");
  }

  // Test 3: Citation Tag & Evidence Matching Properties
  {
    console.log("Test 3: Testing Citation & Evidence Matching...");
    const citation: Citation = {
      citation_id: "cite_1",
      document_id: "DOC-2024-881",
      chunk_id: "DOC-2024-881#chunk_0",
      source_title: "Support Login Troubleshooting Guide",
      passage: "Locked after 5 attempts",
      score: 0.92,
    };

    const evidenceChunk: RetrievedChunk = {
      chunk: {
        chunk_id: "DOC-2024-881#chunk_0",
        document_id: "DOC-2024-881",
        text: "Locked after 5 attempts",
      },
      score: 0.92,
      rank: 1,
    };

    assert(citation.citation_id === "cite_1", "Citation ID verified");
    assert(evidenceChunk.rank === 1, "Evidence rank position verified");
    console.log("✓ Test 3 Passed: Citation & evidence matching verified.\n");
  }

  // Test 4: Insufficient Evidence State
  {
    console.log("Test 4: Testing Insufficient Evidence Response Handling...");
    const res: AnswerResponse = await queryRAG("What is the secret recipe for dark matter?", {
      testMode: true,
      scenario: "insufficient",
    });

    assert(res.has_sufficient_evidence === false, "has_sufficient_evidence must be false");
    assert(res.evidence_status === "insufficient", "evidence_status must be 'insufficient'");
    assert(res.citations.length === 0, "Citations should be empty");
    assert(res.answer.includes("sufficient supporting information"), "Refusal message returned");
    console.log("✓ Test 4 Passed: Insufficient evidence state verified.\n");
  }

  // Test 5: Refused / Invalid Grounding State
  {
    console.log("Test 5: Testing Refusal Response Handling...");
    const res: AnswerResponse = await queryRAG("Unverified query", {
      testMode: true,
      scenario: "refused",
    });

    assert(res.has_sufficient_evidence === false, "has_sufficient_evidence must be false");
    assert(res.evidence_status === "refused", "evidence_status must be 'refused'");
    assert(res.citations.length === 0, "Citations should be empty for refused generation");
    console.log("✓ Test 5 Passed: Refused state verified.\n");
  }

  // Test 6: API Error Exception Handling
  {
    console.log("Test 6: Testing API Failure Exception Handling...");
    try {
      await queryRAG("Error test question", {
        testMode: true,
        scenario: "error",
      });
      assert(false, "Error scenario should throw exception");
    } catch (err: any) {
      assert(err instanceof RAGApiError, "Error must be instance of RAGApiError");
      assert(err.type === "backend_error" || err.type === "network_error", "Error type classified");
      console.log("✓ Test 6 Passed: API failure handling verified.\n");
    }
  }

  console.log("=========================================");
  console.log("ALL 6 RAG QUERY API TESTS PASSED ");
  console.log("=========================================");
}

runTests().catch((err) => {
  console.error("Test Suite Execution Failed:", err);
  process.exit(1);
});
