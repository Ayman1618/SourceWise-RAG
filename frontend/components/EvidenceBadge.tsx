import React from "react";
import { CheckCircle2, FileSearch, ShieldCheck } from "lucide-react";

export function EvidenceBadge() {
  return (
    <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-md bg-slate-100 border border-slate-200 text-slate-700 text-xs font-medium tracking-wide uppercase">
      <span className="flex items-center space-x-1">
        <FileSearch className="w-3.5 h-3.5 text-slate-600" />
        <span>Retrieve</span>
      </span>
      <span className="text-slate-300">•</span>
      <span className="flex items-center space-x-1">
        <ShieldCheck className="w-3.5 h-3.5 text-slate-600" />
        <span>Ground</span>
      </span>
      <span className="text-slate-300">•</span>
      <span className="flex items-center space-x-1">
        <CheckCircle2 className="w-3.5 h-3.5 text-slate-600" />
        <span>Verify</span>
      </span>
    </div>
  );
}
