"use client";

import React, { useState } from "react";
import { Citation, EvidenceStatus } from "@/lib/types/rag";
import { ShieldCheck, Copy, Check, Sparkles, AlertCircle } from "lucide-react";

interface AnswerPanelProps {
  answer: string;
  citations: Citation[];
  confidenceScore?: number | null;
  evidenceStatus?: EvidenceStatus;
  onSelectCitation: (citationId: string) => void;
}

export function AnswerPanel({
  answer,
  citations,
  confidenceScore,
  evidenceStatus = "sufficient",
  onSelectCitation,
}: AnswerPanelProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  /**
   * Helper function to parse citation references like [1], [2], or [cite_1]
   * and render them as interactive buttons linked to the evidence items.
   */
  const renderFormattedAnswer = (text: string) => {
    const parts = text.split(/(\[\w+\])/g);

    return parts.map((part, idx) => {
      const match = part.match(/^\[(\w+)\]$/);
      if (match) {
        const citationId = match[1];
        const exists = citations.some(
          (c) => c.citation_id === citationId || c.citation_id === `cite_${citationId}`
        );

        return (
          <button
            key={idx}
            type="button"
            onClick={() => onSelectCitation(citationId)}
            title={`View Evidence [${citationId}]`}
            className={`inline-flex items-center px-1.5 py-0.5 mx-0.5 text-xs font-mono font-bold rounded transition-colors focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-1 ${
              exists
                ? "bg-brand-900 hover:bg-brand-800 text-white shadow-xs"
                : "bg-slate-800 hover:bg-slate-700 text-white"
            }`}
          >
            [{citationId}]
          </button>
        );
      }
      return <span key={idx}>{part}</span>;
    });
  };

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 sm:p-6 shadow-sm space-y-4">
      {/* Panel Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3 flex-wrap gap-2">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="w-5 h-5 text-brand-900" />
          <h3 className="text-base font-bold text-slate-900 tracking-tight">
            Answer
          </h3>
        </div>

        <div className="flex items-center space-x-2 flex-wrap gap-1.5">
          {confidenceScore !== undefined && confidenceScore !== null && (
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
              Confidence: {Math.round(confidenceScore * 100)}%
            </span>
          )}

          <span
            className={`inline-flex items-center space-x-1 text-xs font-medium px-2.5 py-0.5 rounded border ${
              evidenceStatus === "sufficient"
                ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                : "bg-amber-50 text-amber-700 border-amber-200"
            }`}
          >
            {evidenceStatus === "sufficient" ? (
              <>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>Grounded Answer</span>
              </>
            ) : (
              <>
                <AlertCircle className="w-3 h-3 text-amber-600" />
                <span>Status: {evidenceStatus}</span>
              </>
            )}
          </span>

          <button
            type="button"
            onClick={handleCopy}
            className="p-1.5 rounded text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            title="Copy answer text"
          >
            {copied ? (
              <Check className="w-4 h-4 text-emerald-600" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Answer Content */}
      <div className="text-slate-800 text-base leading-relaxed font-normal">
        {renderFormattedAnswer(answer)}
      </div>

      {/* Footer Info */}
      <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
        <span className="flex items-center space-x-1">
          <Sparkles className="w-3.5 h-3.5 text-slate-400" />
          <span>Click citation tags like [1] to highlight supporting evidence</span>
        </span>
      </div>
    </div>
  );
}
