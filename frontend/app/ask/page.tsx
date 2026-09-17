"use client";

import React, { useState } from "react";
import { getMockRAGResponse, RAGResponse } from "@/lib/mock-data";
import { QuestionInput } from "@/components/ask/QuestionInput";
import { AnswerPanel } from "@/components/ask/AnswerPanel";
import { EvidencePanel } from "@/components/ask/EvidencePanel";
import {
  InsufficientEvidenceNotice,
  ErrorNotice,
  ScenarioSelector,
} from "@/components/ask/AskStates";
import { HelpCircle, RefreshCw } from "lucide-react";

export default function AskPage() {
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<RAGResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [scenario, setScenario] = useState<"normal" | "insufficient" | "error">(
    "normal"
  );
  const [highlightedCitationId, setHighlightedCitationId] = useState<
    string | null
  >(null);

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isLoading) return;

    setIsLoading(true);
    setError(null);
    setResponse(null);
    setHighlightedCitationId(null);

    try {
      const result = await getMockRAGResponse(question, scenario);
      setResponse(result);
    } catch (err: any) {
      setError(
        err?.message || "Something went wrong while processing your question."
      );
    } finally {
      setIsLoading(false);
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
    setError(null);
    setHighlightedCitationId(null);
  };

  return (
    <div className="py-8 sm:py-12 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
            Ask SourceWise
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Grounded enterprise documentation retrieval with explicit citation verification.
          </p>
        </div>

        {/* Action Controls */}
        {(response || error) && (
          <button
            type="button"
            onClick={handleReset}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded bg-white text-slate-700 hover:bg-slate-50 border border-slate-300 text-xs font-medium transition-colors shadow-sm self-start md:self-auto"
          >
            <RefreshCw className="w-3.5 h-3.5 text-slate-500" />
            <span>New Investigation</span>
          </button>
        )}
      </div>

      {/* Scenario Selector Bar for Reviewers & Testing */}
      <ScenarioSelector scenario={scenario} setScenario={setScenario} />

      {/* Question Input Section */}
      <QuestionInput
        question={question}
        setQuestion={setQuestion}
        onSubmit={handleAsk}
        isLoading={isLoading}
      />

      {/* Results / Error / Insufficient Evidence Section */}
      {error && (
        <ErrorNotice
          errorMessage={error}
          onRetry={() => handleAsk(new Event("submit") as any)}
        />
      )}

      {response && (
        <div className="space-y-6 animate-in fade-in-50 duration-300">
          {!response.hasSufficientEvidence ? (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-7">
                <InsufficientEvidenceNotice onReset={handleReset} />
              </div>
              <div className="lg:col-span-5">
                <EvidencePanel
                  citations={[]}
                  highlightedCitationId={null}
                />
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
              {/* Left Main Column: Answer Panel */}
              <div className="lg:col-span-7">
                <AnswerPanel
                  answer={response.answer}
                  citations={response.citations}
                  onSelectCitation={handleSelectCitation}
                />
              </div>

              {/* Right Side Column: Evidence Panel */}
              <div className="lg:col-span-5">
                <EvidencePanel
                  citations={response.citations}
                  highlightedCitationId={highlightedCitationId}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Default State Helper Notice if no results yet */}
      {!response && !error && !isLoading && (
        <div className="p-4 rounded-md bg-slate-100 border border-slate-200 text-xs text-slate-600 flex items-start space-x-2.5">
          <HelpCircle className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-slate-800">
              Evidence-First RAG Architecture:
            </span>{" "}
            Submit your support question above to retrieve verified internal documentation passages. Citations like [1] link directly to supporting evidence excerpts.
          </div>
        </div>
      )}
    </div>
  );
}
