"use client";

import React, { useState } from "react";
import { Citation } from "@/lib/mock-data";
import { ShieldCheck, Copy, Check, Sparkles } from "lucide-react";

interface AnswerPanelProps {
  answer: string;
  citations: Citation[];
  onSelectCitation: (citationId: string) => void;
}

export function AnswerPanel({
  answer,
  citations,
  onSelectCitation,
}: AnswerPanelProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  /**
   * Helper function to parse citation references like [1] or [2]
   * and render them as interactive buttons.
   */
  const renderFormattedAnswer = (text: string) => {
    const parts = text.split(/(\[\d+\])/g);

    return parts.map((part, idx) => {
      const match = part.match(/^\[(\d+)\]$/);
      if (match) {
        const citationId = match[1];
        const exists = citations.some((c) => c.id === citationId);
        if (exists) {
          return (
            <button
              key={idx}
              type="button"
              onClick={() => onSelectCitation(citationId)}
              title={`View Evidence [${citationId}]`}
              className="inline-flex items-center px-1.5 py-0.5 mx-0.5 text-xs font-mono font-bold rounded bg-slate-900 hover:bg-slate-800 text-white transition-colors focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-1"
            >
              [{citationId}]
            </button>
          );
        }
      }
      return <span key={idx}>{part}</span>;
    });
  };

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 sm:p-6 shadow-sm space-y-4">
      {/* Panel Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="w-5 h-5 text-brand-900" />
          <h3 className="text-base font-bold text-slate-900 tracking-tight">
            Answer
          </h3>
        </div>
        <div className="flex items-center space-x-2">
          <span className="inline-flex items-center space-x-1 text-xs font-medium px-2.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>Grounded Response</span>
          </span>
          <button
            type="button"
            onClick={handleCopy}
            className="p-1.5 rounded text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            title="Copy answer"
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
          <span>Click any citation tag like [1] to inspect supporting evidence</span>
        </span>
      </div>
    </div>
  );
}
