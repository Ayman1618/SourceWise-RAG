import React from "react";
import Link from "next/link";
import { ShieldCheck, UserPlus } from "lucide-react";

export function Header() {
  return (
    <header className="border-b border-slate-200 bg-white sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="w-8 h-8 rounded bg-brand-900 flex items-center justify-center text-white shadow-sm group-hover:bg-brand-800 transition-colors">
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
        </Link>

        <nav className="flex items-center space-x-4 text-sm font-medium">
          <Link
            href="/signup"
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-slate-900 text-white hover:bg-slate-800 transition-colors text-xs font-medium shadow-sm"
          >
            <UserPlus className="w-3.5 h-3.5" />
            <span>Sign Up</span>
          </Link>
        </nav>
      </div>
    </header>
  );
}
