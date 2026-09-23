"use client";

import React, { useState } from "react";
import { queryRAG, RAGApiError } from "@/lib/api-client";
import { AnswerResponse, AskUIState } from "@/lib/types/rag";
import { QuestionInput } from "@/components/ask/QuestionInput";
import { AnswerPanel } from "@/components/ask/AnswerPanel";
import { EvidencePanel } from "@/components/ask/EvidencePanel";
import {
  InsufficientEvidenceNotice,
  ErrorNotice,
  SupportAgentLoadingState,
} from "@/components/ask/AskStates";
import { HelpCircle, RefreshCw, Server } from "lucide-react";
import { API_CONFIG } from "@/lib/config";

export default function AskPage() {
  const [question, setQuestion] = useState("");
  const [uiState, setUiState] = useState<AskUIState>("idle");
  const [response, setResponse] = useState<AnswerResponse | null>(null);
  const [errorDetails, setErrorDetails] = useState<{
    type: string;
    message: string;
  } | null>(null);
  const [highlightedCitationId, setHighlightedCitationId] = useState<string | null>(null);

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || uiState === "submitting") return;

    setUiState("submitting");
    setErrorDetails(null);
    setResponse(null);
    setHighlightedCitationId(null);

    try {
      const result = await queryRAG(question);

      setResponse(result);

      if (!result.has_sufficient_evidence || result.evidence_status === "insufficient" || result.evidence_status === "refused") {
        setUiState("insufficient");
      } else {
        setUiState("success");
      }
    } catch (err: any) {
      if (err instanceof RAGApiError) {
        setErrorDetails({
          type: err.type,
          message: err.message,
        });
      } else {
        setErrorDetails({
          type: "backend_error",
          message: err?.message || "An unexpected error occurred while processing your question.",
        });
      }
      setUiState("error");
    }
  };

  const handleSelectCitation = (citationId: string) => {
    setHighlightedCitationId(citationId);
    const element = document.getElementById(`evidence-${citationId}`);
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  };

  const handleReset = () => {
    setQuestion("");
    setResponse(null);
    setErrorDetails(null);
    setHighlightedCitationId(null);
    setUiState("idle");
  };

  return (
    <div className="py-8 sm:py-12 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
              Ask SourceWise
            </h1>
            <span className="text-[11px] font-mono font-medium px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
              Live RAG Query API
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-600">
            Grounded enterprise documentation retrieval with explicit citation verification.
          </p>
        </div>

        {/* Target Backend API Indicator */}
        <div className="flex items-center space-x-3 flex-wrap gap-y-2">
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded bg-slate-100 border border-slate-200 text-slate-600 text-xs font-mono">
            <Server className="w-3.5 h-3.5 text-slate-500" />
            <span className="truncate max-w-[200px]">{API_CONFIG.baseUrl}</span>
          </span>

          {uiState !== "idle" && (
            <button
              type="button"
              onClick={handleReset}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded bg-white text-slate-700 hover:bg-slate-50 border border-slate-300 text-xs font-medium transition-colors shadow-xs"
            >
              <RefreshCw className="w-3.5 h-3.5 text-slate-500" />
              <span>New Investigation</span>
            </button>
          )}
        </div>
      </div>

      {/* Question Input Component */}
      <QuestionInput
        question={question}
        setQuestion={setQuestion}
        onSubmit={handleAsk}
        isLoading={uiState === "submitting"}
      />

      {/* State: Submitting Loading State */}
      {uiState === "submitting" && <SupportAgentLoadingState />}

      {/* State: Error State */}
      {uiState === "error" && errorDetails && (
        <ErrorNotice
          errorType={errorDetails.type}
          errorMessage={errorDetails.message}
          onRetry={() => handleAsk(new Event("submit") as any)}
        />
      )}

      {/* State: Insufficient Evidence State */}
      {uiState === "insufficient" && response && (
        <div className="space-y-6 animate-in fade-in-50 duration-300">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-7">
              <InsufficientEvidenceNotice onReset={handleReset} />
            </div>
            <div className="lg:col-span-5">
              <EvidencePanel
                citations={response.citations}
                evidence={response.evidence}
                highlightedCitationId={null}
              />
            </div>
          </div>
        </div>
      )}

      {/* State: Success State */}
      {uiState === "success" && response && (
        <div className="space-y-6 animate-in fade-in-50 duration-300">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left Main Column: Answer Panel */}
            <div className="lg:col-span-7">
              <AnswerPanel
                answer={response.answer}
                citations={response.citations}
                confidenceScore={response.confidence_score}
                evidenceStatus={response.evidence_status}
                onSelectCitation={handleSelectCitation}
              />
            </div>

            {/* Right Side Column: Evidence Panel */}
            <div className="lg:col-span-5">
              <EvidencePanel
                citations={response.citations}
                evidence={response.evidence}
                highlightedCitationId={highlightedCitationId}
              />
            </div>
          </div>
        </div>
      )}

      {/* State: Idle State Notice */}
      {uiState === "idle" && (
        <div className="p-4 rounded-md bg-slate-100 border border-slate-200 text-xs text-slate-600 flex items-start space-x-2.5">
          <HelpCircle className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-slate-800">
              Live RAG Query API Connected:
            </span>{" "}
            Submitting a question executes `POST /api/v1/query` against `{API_CONFIG.baseUrl}`. The answer, citations, and evidence are populated directly from the backend response contract.
          </div>
        </div>
      )}
    </div>
  );
}
