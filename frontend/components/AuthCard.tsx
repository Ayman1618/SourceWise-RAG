import React from "react";
import Link from "next/link";
import { ShieldCheck } from "lucide-react";

interface AuthCardProps {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}

export function AuthCard({ title, subtitle, children }: AuthCardProps) {
  return (
    <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-lg border border-slate-200 shadow-sm">
        <div className="text-center">
          <Link href="/" className="inline-flex w-12 h-12 rounded bg-brand-900 items-center justify-center text-white shadow-sm mb-4 hover:bg-brand-800 transition-colors">
            <ShieldCheck className="w-6 h-6 text-slate-100" />
          </Link>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">
            {title}
          </h2>
          <p className="mt-2 text-sm text-slate-600">
            {subtitle}
          </p>
        </div>

        {children}

        <div className="pt-4 border-t border-slate-100 text-center space-y-3">
          <p className="text-xs text-slate-500">
            Access to SourceWise RAG is governed by enterprise document security policies.
          </p>
          <div className="text-xs">
            <Link href="/" className="font-medium text-slate-700 hover:text-slate-900 underline">
              ← Return to Home
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
