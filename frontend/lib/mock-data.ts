export interface Citation {
  id: string;
  documentId: string;
  title: string;
  sourceType: string;
  version: string;
  passage: string;
}

export interface RAGResponse {
  question: string;
  answer: string;
  citations: Citation[];
  hasSufficientEvidence: boolean;
  retrievedAt?: string;
}

export const SAMPLE_QUESTIONS = [
  "How do I troubleshoot repeated login failures?",
  "What is the procedure for emergency database failover?",
  "What are the compliance requirements for customer data retention?",
];

export const MOCK_SUCCESS_RESPONSE: RAGResponse = {
  question: "How do I troubleshoot repeated login failures?",
  answer:
    "Repeated login failures can be caused by incorrect credentials, an expired session, or account lockout [1]. Check the user's authentication status and follow the documented recovery procedure [2]. If credentials are confirmed valid, verify whether active IP security flags or token expiration are blocking access [2].",
  hasSufficientEvidence: true,
  retrievedAt: "Just now",
  citations: [
    {
      id: "1",
      documentId: "DOC-2024-881",
      title: "Support Login Troubleshooting Guide",
      sourceType: "Support Documentation",
      version: "v2.1",
      passage:
        "Verify whether the account has been temporarily locked after repeated unsuccessful authentication attempts. Default security policy locks accounts after 5 failed attempts within 15 minutes.",
    },
    {
      id: "2",
      documentId: "DOC-2024-412",
      title: "Identity & Access Management Protocol",
      sourceType: "Security Standard",
      version: "v1.4",
      passage:
        "If credentials are correct but authentication fails, verify session token expiration or active IP security flags before initiating password reset or account recovery procedures.",
    },
  ],
};

export const MOCK_INSUFFICIENT_EVIDENCE_RESPONSE: RAGResponse = {
  question: "",
  answer:
    "I couldn't find sufficient supporting information in the available knowledge base to answer this reliably.",
  hasSufficientEvidence: false,
  retrievedAt: "Just now",
  citations: [],
};

/**
 * Simulates a RAG engine query with frontend local delay (no network calls).
 */
export async function getMockRAGResponse(
  question: string,
  scenario: "normal" | "insufficient" | "error" = "normal"
): Promise<RAGResponse> {
  // Simulate lightweight local processing delay (600ms)
  await new Promise((resolve) => setTimeout(resolve, 600));

  if (scenario === "error") {
    throw new Error("Something went wrong while processing your question.");
  }

  if (scenario === "insufficient") {
    return {
      ...MOCK_INSUFFICIENT_EVIDENCE_RESPONSE,
      question,
    };
  }

  return {
    ...MOCK_SUCCESS_RESPONSE,
    question,
  };
}
