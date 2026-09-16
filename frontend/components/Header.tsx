import React from "react";
import { ShieldCheck } from "lucide-react";

export function Header() {
  return (
    <header className="border-b border-slate-200 bg-white sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded bg-brand-900 flex items-center justify-center text-white shadow-sm">
            <ShieldCheck className="w-5 h-5 text-slate-100" />
          </div>
          <div>
            <span className="font-semibold text-slate-900 tracking-tight text-lg">
              SourceWise RAG
            </span>
            <span className="ml-2 hidden sm:inline-block text-xs font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
              Foundation v0.1
            </span>
          </div>
        </div>

        <nav className="flex items-center space-x-6 text-sm font-medium text-slate-600">
          <span className="hidden md:inline-block text-slate-500 text-xs tracking-wide uppercase font-mono">
            Enterprise Knowledge Assistant
          </span>
        </nav>
      </div>
    </header>
  );
}
