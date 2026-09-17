"use client";

import React from "react";
import { Citation } from "@/lib/mock-data";
import { FileText, Tag, ShieldCheck } from "lucide-react";

interface EvidenceItemProps {
  citation: Citation;
  isHighlighted?: boolean;
}

export function EvidenceItem({ citation, isHighlighted }: EvidenceItemProps) {
  return (
    <div
      id={`evidence-${citation.id}`}
      className={`p-4 rounded-md border transition-all duration-300 ${
        isHighlighted
          ? "border-brand-600 bg-brand-50/60 ring-2 ring-brand-500/20 shadow-sm"
          : "border-slate-200 bg-white hover:border-slate-300"
      }`}
    >
      {/* Header Info */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center space-x-2 flex-wrap gap-y-1">
          <span className="inline-flex items-center justify-center font-mono font-semibold text-xs px-2 py-0.5 rounded bg-slate-900 text-white">
            [{citation.id}]
          </span>
          <h4 className="text-sm font-semibold text-slate-900 leading-snug">
            {citation.title}
          </h4>
        </div>
        <span className="text-[11px] font-mono text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200 shrink-0">
          {citation.version}
        </span>
      </div>

      {/* Metadata Badges */}
      <div className="flex items-center space-x-3 text-xs text-slate-500 mb-3">
        <span className="inline-flex items-center space-x-1">
          <FileText className="w-3.5 h-3.5 text-slate-400" />
          <span>{citation.sourceType}</span>
        </span>
        <span>•</span>
        <span className="inline-flex items-center space-x-1 font-mono text-[11px]">
          <Tag className="w-3 h-3 text-slate-400" />
          <span>{citation.documentId}</span>
        </span>
      </div>

      {/* Passage Excerpt */}
      <blockquote className="p-3 bg-slate-50 border-l-2 border-slate-400 rounded-r text-xs sm:text-sm text-slate-700 leading-relaxed italic">
        &ldquo;{citation.passage}&rdquo;
      </blockquote>

      {/* Verification footer */}
      <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-100">
        <span className="inline-flex items-center space-x-1 text-slate-600 font-medium">
          <ShieldCheck className="w-3 h-3 text-emerald-600" />
          <span>Verified Passage Excerpt</span>
        </span>
        <span className="text-slate-400">Grounding Confidence: High</span>
      </div>
    </div>
  );
}
