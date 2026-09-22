import React from "react";
import { BookOpen, Database, ShieldCheck } from "lucide-react";

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
              Knowledge Base
            </h1>
            <span className="text-[11px] font-mono font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
              Repository Catalog
            </span>
          </div>
          <p className="mt-1.5 text-sm text-slate-600 max-w-2xl leading-relaxed">
            Enterprise knowledge sources, specifications, and runbooks indexed for grounded RAG retrieval and citation verification.
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
    </div>
  );
}
