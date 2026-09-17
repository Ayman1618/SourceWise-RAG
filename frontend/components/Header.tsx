"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShieldCheck, MessageSquare, BookOpen, LogIn, UserPlus } from "lucide-react";

export function Header() {
  const pathname = usePathname();

  const isAskActive = pathname === "/ask";

  return (
    <header className="border-b border-slate-200 bg-white sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo & Tagline */}
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="w-8 h-8 rounded bg-brand-900 flex items-center justify-center text-white shadow-sm group-hover:bg-brand-800 transition-colors">
            <ShieldCheck className="w-5 h-5 text-slate-100" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-semibold text-slate-900 tracking-tight text-lg">
                SourceWise RAG
              </span>
              <span className="hidden sm:inline-block text-[10px] font-medium px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200 uppercase tracking-wider">
                v0.2 Ask UX
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-medium tracking-tight hidden md:block">
              Retrieve. Ground. Verify.
            </p>
          </div>
        </Link>

        {/* Primary Navigation Links */}
        <nav className="flex items-center space-x-1 sm:space-x-2 text-sm font-medium">
          <Link
            href="/ask"
            className={`inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              isAskActive
                ? "bg-slate-900 text-white font-semibold shadow-sm"
                : "text-slate-700 hover:bg-slate-100 hover:text-slate-900"
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Ask</span>
          </Link>

          <span
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-slate-400 cursor-not-allowed text-xs font-medium relative group"
            title="Knowledge Base browsing coming soon in future PRs"
          >
            <BookOpen className="w-3.5 h-3.5 text-slate-300" />
            <span>Knowledge Base</span>
            <span className="hidden sm:inline-block text-[9px] uppercase font-mono px-1 py-0.2 bg-slate-100 text-slate-500 rounded border border-slate-200 ml-1">
              Soon
            </span>
          </span>
        </nav>

        {/* Auth Actions */}
        <div className="hidden sm:flex items-center space-x-2 text-xs">
          <Link
            href="/login"
            className="inline-flex items-center space-x-1 px-2.5 py-1.5 rounded text-slate-700 hover:bg-slate-100 font-medium transition-colors"
          >
            <LogIn className="w-3.5 h-3.5 text-slate-500" />
            <span>Sign In</span>
          </Link>
          <Link
            href="/signup"
            className="inline-flex items-center space-x-1 px-3 py-1.5 rounded bg-brand-900 text-white hover:bg-brand-800 font-medium transition-colors shadow-sm"
          >
            <UserPlus className="w-3.5 h-3.5" />
            <span>Sign Up</span>
          </Link>
        </div>
      </div>
    </header>
  );
}
