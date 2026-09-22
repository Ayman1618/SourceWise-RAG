"use client";

import React from "react";
import { Citation, RetrievedChunk } from "@/lib/types/rag";
import { EvidenceItem } from "./EvidenceItem";
import { FileCheck2, Info } from "lucide-react";

interface EvidencePanelProps {
  citations: Citation[];
  evidence?: RetrievedChunk[];
  highlightedCitationId: string | null;
}

export function EvidencePanel({
  citations,
  evidence = [],
  highlightedCitationId,
}: EvidencePanelProps) {
  const itemCount = citations.length > 0 ? citations.length : evidence.length;

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 sm:p-6 shadow-sm space-y-4">
      {/* Panel Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center space-x-2">
          <FileCheck2 className="w-4.5 h-4.5 text-slate-700" />
          <h3 className="text-base font-bold text-slate-900 tracking-tight">
            Evidence & Citations
          </h3>
        </div>
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
          {itemCount} {itemCount === 1 ? "Item" : "Items"} Retrieved
        </span>
      </div>

      {/* Item List */}
      {itemCount > 0 ? (
        <div className="space-y-4">
          {citations.length > 0
            ? citations.map((citation, idx) => (
                <EvidenceItem
                  key={citation.citation_id || idx}
                  citation={citation}
                  retrievedChunk={evidence[idx]}
                  index={idx}
                  isHighlighted={highlightedCitationId === citation.citation_id}
                />
              ))
            : evidence.map((chunk, idx) => (
                <EvidenceItem
                  key={chunk.chunk.chunk_id || idx}
                  retrievedChunk={chunk}
                  index={idx}
                  isHighlighted={highlightedCitationId === String(idx + 1)}
                />
              ))}
        </div>
      ) : (
        <div className="p-6 text-center rounded-md bg-slate-50 border border-dashed border-slate-200 text-slate-500 text-sm space-y-2">
          <Info className="w-5 h-5 text-slate-400 mx-auto" />
          <p className="font-medium text-slate-700">No supporting evidence retrieved</p>
          <p className="text-xs text-slate-500">
            No verified passages from internal documentation met the grounding threshold.
          </p>
        </div>
      )}
    </div>
  );
}
