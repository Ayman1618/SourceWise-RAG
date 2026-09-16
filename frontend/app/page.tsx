import React from "react";
import { EvidenceBadge } from "@/components/EvidenceBadge";
import { ArrowRight, BookOpen, CheckCircle, FileText, Search } from "lucide-react";

export default function Home() {
  return (
    <div className="py-12 sm:py-20 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto">
      {/* Hero Section */}
      <div className="text-center max-w-3xl mx-auto">
        <div className="mb-6 flex justify-center">
          <EvidenceBadge />
        </div>

        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-slate-900 leading-tight">
          SourceWise RAG
        </h1>

        <p className="mt-2 text-xl sm:text-2xl font-medium text-slate-600 tracking-tight">
          Retrieve. Ground. Verify.
        </p>

        <p className="mt-6 text-base sm:text-lg text-slate-600 leading-relaxed max-w-2xl mx-auto">
          A grounded enterprise knowledge assistant that retrieves, verifies, and cites trustworthy information from internal documentation.
        </p>

        {/* Action Buttons */}
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4">
          <button
            type="button"
            className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-3 rounded-md bg-brand-900 hover:bg-brand-800 text-white font-medium text-sm transition-colors duration-150 shadow-sm focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
          >
            <span>Ask a Question</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <button
            type="button"
            className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-3 rounded-md bg-white hover:bg-slate-50 text-slate-700 font-medium text-sm border border-slate-300 transition-colors duration-150 shadow-sm focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2"
          >
            <BookOpen className="w-4 h-4 text-slate-500" />
            <span>Knowledge Base</span>
          </button>
        </div>

        {/* Evidence-First Callout Banner */}
        <div className="mt-10 p-4 rounded-md bg-white border border-slate-200 shadow-sm text-left flex items-start space-x-3 max-w-2xl mx-auto">
          <CheckCircle className="w-5 h-5 text-slate-700 shrink-0 mt-0.5" />
          <p className="text-sm text-slate-700 leading-normal">
            <span className="font-semibold text-slate-900">Evidence-First Assurance:</span> Answers are grounded in retrieved internal sources and linked to supporting passages.
          </p>
        </div>
      </div>

      {/* Product Foundation Highlights */}
      <div className="mt-16 sm:mt-24 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 rounded-md bg-white border border-slate-200 shadow-sm">
          <div className="w-9 h-9 rounded bg-slate-100 flex items-center justify-center text-slate-700 mb-4">
            <Search className="w-5 h-5" />
          </div>
          <h3 className="text-base font-semibold text-slate-900">Retrieve</h3>
          <p className="mt-2 text-sm text-slate-600 leading-relaxed">
            Targeted retrieval across internal enterprise document repositories with high relevance scoring.
          </p>
        </div>

        <div className="p-6 rounded-md bg-white border border-slate-200 shadow-sm">
          <div className="w-9 h-9 rounded bg-slate-100 flex items-center justify-center text-slate-700 mb-4">
            <FileText className="w-5 h-5" />
          </div>
          <h3 className="text-base font-semibold text-slate-900">Ground</h3>
          <p className="mt-2 text-sm text-slate-600 leading-relaxed">
            Strict anchoring of generated responses directly to verified passage excerpts and source metadata.
          </p>
        </div>

        <div className="p-6 rounded-md bg-white border border-slate-200 shadow-sm">
          <div className="w-9 h-9 rounded bg-slate-100 flex items-center justify-center text-slate-700 mb-4">
            <CheckCircle className="w-5 h-5" />
          </div>
          <h3 className="text-base font-semibold text-slate-900">Verify</h3>
          <p className="mt-2 text-sm text-slate-600 leading-relaxed">
            Continuous verification pipelines ensuring factual consistency and citation reliability.
          </p>
        </div>
      </div>
    </div>
  );
}
