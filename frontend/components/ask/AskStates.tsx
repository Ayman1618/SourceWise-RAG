"use client";

import React from "react";
import { AlertTriangle, RefreshCw, AlertCircle, WifiOff, Loader2 } from "lucide-react";

interface InsufficientEvidenceNoticeProps {
  onReset: () => void;
}

export function InsufficientEvidenceNotice({ onReset }: InsufficientEvidenceNoticeProps) {
  return (
    <div className="bg-amber-50 border border-amber-200 rounded-lg p-5 text-slate-800 space-y-3 shadow-xs">
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
      <div className="pt-2.5 border-t border-amber-200/60 flex items-center justify-between text-xs text-amber-700 flex-wrap gap-2">
        <span>Backend Grounding Classification: Insufficient Evidence. Refusal enforced.</span>
        <button
          type="button"
          onClick={onReset}
          className="font-semibold underline hover:text-amber-900"
        >
          Try another question
        </button>
      </div>
    </div>
  );
}

interface ErrorNoticeProps {
  errorType: "network_error" | "backend_error" | "timeout_error" | string;
  errorMessage: string;
  onRetry: () => void;
}

export function ErrorNotice({ errorType, errorMessage, onRetry }: ErrorNoticeProps) {
  const isNetwork = errorType === "network_error";

  return (
    <div className={`border rounded-lg p-5 text-slate-800 space-y-3 shadow-xs ${
      isNetwork ? "bg-slate-900 border-slate-800 text-white" : "bg-red-50 border-red-200"
    }`}>
      <div className="flex items-start space-x-3">
        {isNetwork ? (
          <WifiOff className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        ) : (
          <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
        )}
        <div>
          <h4 className={`text-sm font-bold ${isNetwork ? "text-white" : "text-red-900"}`}>
            {isNetwork ? "Backend API Connection Offline" : "RAG Query Error"}
          </h4>
          <p className={`mt-1 text-sm leading-relaxed ${isNetwork ? "text-slate-300" : "text-red-800"}`}>
            {errorMessage || "An unexpected error occurred while processing your question."}
          </p>
        </div>
      </div>
      <div className={`pt-2.5 border-t flex items-center justify-between flex-wrap gap-2 ${
        isNetwork ? "border-slate-800 text-slate-400 text-xs" : "border-red-200/60 text-xs text-red-700"
      }`}>
        <span>
          {isNetwork
            ? "Ensure the backend FastAPI server is running at NEXT_PUBLIC_API_URL."
            : "Backend query failed. Your request was logged for inspection."}
        </span>
        <button
          type="button"
          onClick={onRetry}
          className={`inline-flex items-center space-x-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors shadow-xs ${
            isNetwork
              ? "bg-amber-500 hover:bg-amber-600 text-slate-950 font-semibold"
              : "bg-red-600 hover:bg-red-700 text-white"
          }`}
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Retry Request</span>
        </button>
      </div>
    </div>
  );
}

export function SupportAgentLoadingState() {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-xs space-y-4">
      <div className="flex items-center space-x-3">
        <Loader2 className="w-5 h-5 animate-spin text-brand-900" />
        <div>
          <h4 className="text-sm font-bold text-slate-900">Executing RAG Pipeline</h4>
          <p className="text-xs text-slate-500">Querying vector store index & synthesizing grounded evidence...</p>
        </div>
      </div>

      <div className="space-y-2 pt-2 border-t border-slate-100">
        <div className="flex items-center space-x-2 text-xs text-slate-600">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></div>
          <span className="font-mono">1/3 Retrieving top matching passages from Qdrant vector store</span>
        </div>
        <div className="flex items-center space-x-2 text-xs text-slate-500">
          <div className="w-2 h-2 rounded-full bg-slate-300"></div>
          <span className="font-mono">2/3 Verifying grounding relevance and passage scores</span>
        </div>
        <div className="flex items-center space-x-2 text-xs text-slate-500">
          <div className="w-2 h-2 rounded-full bg-slate-300"></div>
          <span className="font-mono">3/3 Synthesizing grounded response with citations</span>
        </div>
      </div>
    </div>
  );
}
