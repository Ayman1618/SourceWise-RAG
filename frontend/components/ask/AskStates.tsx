"use client";

import React from "react";
import { AlertTriangle, HelpCircle, RefreshCw, AlertCircle } from "lucide-react";

interface InsufficientEvidenceNoticeProps {
  onReset: () => void;
}

export function InsufficientEvidenceNotice({ onReset }: InsufficientEvidenceNoticeProps) {
  return (
    <div className="bg-amber-50 border border-amber-200 rounded-lg p-5 text-slate-800 space-y-3">
      <div className="flex items-start space-x-3">
        <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div>
          <h4 className="text-sm font-bold text-amber-900">
            Insufficient Supporting Evidence
          </h4>
          <p className="mt-1 text-sm text-amber-800 leading-relaxed">
            I couldn&apos;t find sufficient supporting information in the available knowledge base to answer this reliably.
          </p>
        </div>
      </div>
      <div className="pt-2 border-t border-amber-200/60 flex items-center justify-between text-xs text-amber-700">
        <span>Enterprise Grounding Policy enforced: Refusing ungrounded output.</span>
        <button
          type="button"
          onClick={onReset}
          className="font-medium underline hover:text-amber-900"
        >
          Try another question
        </button>
      </div>
    </div>
  );
}

interface ErrorNoticeProps {
  errorMessage: string;
  onRetry: () => void;
}

export function ErrorNotice({ errorMessage, onRetry }: ErrorNoticeProps) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-5 text-slate-800 space-y-3">
      <div className="flex items-start space-x-3">
        <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
        <div>
          <h4 className="text-sm font-bold text-red-900">Processing Error</h4>
          <p className="mt-1 text-sm text-red-800 leading-relaxed">
            {errorMessage || "Something went wrong while processing your question."}
          </p>
        </div>
      </div>
      <div className="pt-2 border-t border-red-200/60 flex items-center justify-between">
        <span className="text-xs text-red-700">Local mock error state triggered for testing.</span>
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded bg-red-600 text-white text-xs font-medium hover:bg-red-700 transition-colors shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Try again</span>
        </button>
      </div>
    </div>
  );
}

interface ScenarioSelectorProps {
  scenario: "normal" | "insufficient" | "error";
  setScenario: (sc: "normal" | "insufficient" | "error") => void;
}

export function ScenarioSelector({ scenario, setScenario }: ScenarioSelectorProps) {
  return (
    <div className="bg-slate-100 border border-slate-200 rounded-md p-3 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs">
      <div className="flex items-center space-x-2 text-slate-600">
        <HelpCircle className="w-4 h-4 text-slate-500" />
        <span className="font-semibold text-slate-900">UX Test Controls:</span>
        <span className="hidden md:inline text-slate-500">
          Toggle frontend mock states for verification
        </span>
      </div>
      <div className="flex items-center space-x-1.5 w-full sm:w-auto">
        <button
          type="button"
          onClick={() => setScenario("normal")}
          className={`flex-1 sm:flex-initial px-2.5 py-1 rounded text-xs font-medium transition-colors border ${
            scenario === "normal"
              ? "bg-slate-900 text-white border-slate-900"
              : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
          }`}
        >
          Normal Answer
        </button>
        <button
          type="button"
          onClick={() => setScenario("insufficient")}
          className={`flex-1 sm:flex-initial px-2.5 py-1 rounded text-xs font-medium transition-colors border ${
            scenario === "insufficient"
              ? "bg-amber-600 text-white border-amber-600"
              : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
          }`}
        >
          Insufficient Evidence
        </button>
        <button
          type="button"
          onClick={() => setScenario("error")}
          className={`flex-1 sm:flex-initial px-2.5 py-1 rounded text-xs font-medium transition-colors border ${
            scenario === "error"
              ? "bg-red-600 text-white border-red-600"
              : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
          }`}
        >
          Error State
        </button>
      </div>
    </div>
  );
}
