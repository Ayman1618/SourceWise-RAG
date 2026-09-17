"use client";

import React from "react";
import { Citation } from "@/lib/mock-data";
import { EvidenceItem } from "./EvidenceItem";
import { FileCheck2, Info } from "lucide-react";

interface EvidencePanelProps {
  citations: Citation[];
  highlightedCitationId: string | null;
}

export function EvidencePanel({
  citations,
  highlightedCitationId,
}: EvidencePanelProps) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 sm:p-6 shadow-sm space-y-4">
      {/* Panel Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2">
          <FileCheck2 className="w-4 h-4 text-slate-700" />
          <h3 className="text-base font-bold text-slate-900 tracking-tight">
            Evidence
          </h3>
        </div>
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
          {citations.length} {citations.length === 1 ? "Source" : "Sources"} Retrieved
        </span>
      </div>

      {/* Citations List */}
      {citations.length > 0 ? (
        <div className="space-y-4">
          {citations.map((citation) => (
            <EvidenceItem
              key={citation.id}
              citation={citation}
              isHighlighted={highlightedCitationId === citation.id}
            />
          ))}
        </div>
      ) : (
        <div className="p-6 text-center rounded-md bg-slate-50 border border-dashed border-slate-200 text-slate-500 text-sm space-y-2">
          <Info className="w-5 h-5 text-slate-400 mx-auto" />
          <p className="font-medium text-slate-700">No supporting evidence retrieved</p>
          <p className="text-xs text-slate-500">
            No verified passages from internal documentation met the grounding relevance threshold.
          </p>
        </div>
      )}
    </div>
  );
}
