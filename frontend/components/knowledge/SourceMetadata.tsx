import React from "react";
import { Tag, Calendar, User, Layers, ShieldCheck, FileCheck } from "lucide-react";
import { AccessLevel } from "@/lib/knowledge-data";

interface SourceMetadataProps {
  id: string;
  product: string;
  version: string;
  lastUpdated: string;
  department: string;
  accessLevel?: AccessLevel;
  chunkCount?: number;
}

export function SourceMetadata({
  id,
  product,
  version,
  lastUpdated,
  department,
  accessLevel,
  chunkCount,
}: SourceMetadataProps) {
  return (
    <div className="flex items-center space-x-2.5 text-xs text-slate-500 flex-wrap gap-y-1.5">
      <span className="inline-flex items-center space-x-1 font-mono font-semibold text-slate-700 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">
        <Tag className="w-3 h-3 text-slate-400" />
        <span>{id}</span>
      </span>

      <span className="inline-flex items-center space-x-1 text-slate-600 font-medium">
        <Layers className="w-3 h-3 text-slate-400" />
        <span>{product}</span>
      </span>

      <span>•</span>

      <span className="font-mono text-[11px] text-slate-500 bg-slate-50 px-1.5 py-0.5 rounded border border-slate-200">
        {version}
      </span>

      <span>•</span>

      <span className="inline-flex items-center space-x-1">
        <User className="w-3 h-3 text-slate-400" />
        <span>{department}</span>
      </span>

      {accessLevel && (
        <>
          <span>•</span>
          <span className="inline-flex items-center space-x-1 px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 font-mono text-[10px] border border-slate-200">
            <ShieldCheck className="w-3 h-3 text-emerald-600" />
            <span>{accessLevel}</span>
          </span>
        </>
      )}

      <span>•</span>

      <span className="inline-flex items-center space-x-1">
        <Calendar className="w-3 h-3 text-slate-400" />
        <span>Updated {lastUpdated}</span>
      </span>

      {chunkCount !== undefined && (
        <>
          <span>•</span>
          <span className="text-[11px] font-mono text-slate-600">
            {chunkCount} Chunks
          </span>
        </>
      )}
    </div>
  );
}
