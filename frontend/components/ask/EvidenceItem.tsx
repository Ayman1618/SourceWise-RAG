"use client";

import React from "react";
import { Citation, RetrievedChunk } from "@/lib/types/rag";
import { FileText, Tag, ShieldCheck, ExternalLink } from "lucide-react";

interface EvidenceItemProps {
  citation?: Citation;
  retrievedChunk?: RetrievedChunk;
  index: number;
  isHighlighted?: boolean;
}

export function EvidenceItem({
  citation,
  retrievedChunk,
  index,
  isHighlighted,
}: EvidenceItemProps) {
  const citationId = citation?.citation_id || String(index + 1);
  const title = citation?.source_title || retrievedChunk?.chunk.metadata?.title || "Internal Source Document";
  const documentId = citation?.document_id || retrievedChunk?.chunk.document_id || `DOC-${index + 1}`;
  const chunkId = citation?.chunk_id || retrievedChunk?.chunk.chunk_id || `chunk_${index}`;
  const passage = citation?.passage || retrievedChunk?.chunk.text || "";
  const sourcePath = citation?.source_path;
  const sourceType = (retrievedChunk?.chunk.metadata?.source_type as string) || "Support Document";
  const version = (retrievedChunk?.chunk.metadata?.version as string) || "v1.0";
  const score = citation?.score ?? retrievedChunk?.score;

  return (
    <div
      id={`evidence-${citationId}`}
      className={`p-4 rounded-md border transition-all duration-300 ${
        isHighlighted
          ? "border-brand-600 bg-brand-50/70 ring-2 ring-brand-500/20 shadow-sm"
          : "border-slate-200 bg-white hover:border-slate-300 shadow-xs"
      }`}
    >
      {/* Header Row */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center space-x-2 flex-wrap gap-y-1">
          <span className="inline-flex items-center justify-center font-mono font-semibold text-xs px-2 py-0.5 rounded bg-slate-900 text-white">
            [{citationId}]
          </span>
          <h4 className="text-sm font-semibold text-slate-900 leading-snug">
            {title}
          </h4>
        </div>
        <div className="flex items-center space-x-1.5 shrink-0">
          {score !== undefined && score !== null && (
            <span className="text-[11px] font-mono font-medium px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
              {Math.round(score * 100)}% Match
            </span>
          )}
          <span className="text-[11px] font-mono text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">
            {version}
          </span>
        </div>
      </div>

      {/* Metadata Row */}
      <div className="flex items-center space-x-3 text-xs text-slate-500 mb-3 flex-wrap gap-y-1">
        <span className="inline-flex items-center space-x-1">
          <FileText className="w-3.5 h-3.5 text-slate-400" />
          <span>{sourceType}</span>
        </span>
        <span>•</span>
        <span className="inline-flex items-center space-x-1 font-mono text-[11px]">
          <Tag className="w-3 h-3 text-slate-400" />
          <span>{documentId}</span>
        </span>
        {chunkId && (
          <>
            <span>•</span>
            <span className="font-mono text-[11px] text-slate-400">{chunkId}</span>
          </>
        )}
      </div>

      {/* Supporting Passage Excerpt */}
      <blockquote className="p-3 bg-slate-50 border-l-2 border-slate-400 rounded-r text-xs sm:text-sm text-slate-700 leading-relaxed italic">
        &ldquo;{passage}&rdquo;
      </blockquote>

      {/* Footer Info & Provenance */}
      <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-100">
        <span className="inline-flex items-center space-x-1 text-slate-600 font-medium">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          <span>Verifiable Evidence Chunk</span>
        </span>
        {sourcePath && (
          <span className="inline-flex items-center space-x-1 font-mono text-slate-400 truncate max-w-[200px]" title={sourcePath}>
            <ExternalLink className="w-3 h-3 shrink-0" />
            <span className="truncate">{sourcePath}</span>
          </span>
        )}
      </div>
    </div>
  );
}
