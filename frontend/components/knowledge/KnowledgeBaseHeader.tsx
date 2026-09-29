import React from "react";
import { BookOpen, Database, ShieldCheck, ArrowRight, Layers } from "lucide-react";

interface KnowledgeBaseHeaderProps {
  totalDocs: number;
}

export function KnowledgeBaseHeader({ totalDocs }: KnowledgeBaseHeaderProps) {
  return (
    <div className="border-b border-slate-200 pb-5 space-y-4">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <div className="w-7 h-7 rounded bg-brand-900 flex items-center justify-center text-white shadow-xs">
              <BookOpen className="w-4 h-4" />
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
              Knowledge Base Catalog
            </h1>
            <span className="text-[11px] font-mono font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200 uppercase tracking-wider">
              Enterprise Sources
            </span>
          </div>
          <p className="mt-1.5 text-sm text-slate-600 max-w-2xl leading-relaxed">
            Explore indexed internal documentation, technical specifications, and operations runbooks available for RAG retrieval and citation grounding.
          </p>
        </div>

        {/* Stats Badges */}
        <div className="flex items-center space-x-3 text-xs">
          <div className="p-2.5 rounded-md bg-white border border-slate-200 shadow-xs flex items-center space-x-2">
            <Database className="w-4 h-4 text-slate-500" />
            <div>
              <p className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">Indexed Sources</p>
              <p className="font-semibold text-slate-900 font-mono text-sm">{totalDocs} Documents</p>
            </div>
          </div>

          <div className="p-2.5 rounded-md bg-white border border-slate-200 shadow-xs flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <div>
              <p className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">Verification</p>
              <p className="font-semibold text-slate-900 text-sm">Grounding Active</p>
            </div>
          </div>
        </div>
      </div>

      {/* Evidence-First Architecture Workflow Indicator */}
      <div className="bg-slate-50 rounded-md border border-slate-200 px-4 py-2.5 flex items-center justify-between text-xs text-slate-600 flex-wrap gap-2">
        <div className="flex items-center space-x-2 font-medium">
          <Layers className="w-4 h-4 text-brand-900" />
          <span>Evidence-First RAG Flow:</span>
        </div>
        <div className="flex items-center space-x-2 font-mono text-[11px]">
          <span className="bg-white px-2 py-0.5 rounded border border-slate-200 text-slate-800 font-semibold">1. Knowledge Source</span>
          <ArrowRight className="w-3 h-3 text-slate-400" />
          <span className="bg-white px-2 py-0.5 rounded border border-slate-200 text-slate-800 font-semibold">2. Qdrant Chunk Retrieval</span>
          <ArrowRight className="w-3 h-3 text-slate-400" />
          <span className="bg-white px-2 py-0.5 rounded border border-slate-200 text-slate-800 font-semibold">3. Grounded Answer + Citation</span>
        </div>
      </div>
    </div>
  );
}
