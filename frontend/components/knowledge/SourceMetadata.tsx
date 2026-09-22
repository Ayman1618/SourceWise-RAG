import React from "react";
import { Tag, Calendar, User, Layers } from "lucide-react";

interface SourceMetadataProps {
  id: string;
  product: string;
  version: string;
  lastUpdated: string;
  department: string;
  chunkCount?: number;
}

export function SourceMetadata({
  id,
  product,
  version,
  lastUpdated,
  department,
  chunkCount,
}: SourceMetadataProps) {
  return (
    <div className="flex items-center space-x-3 text-xs text-slate-500 flex-wrap gap-y-1.5">
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
