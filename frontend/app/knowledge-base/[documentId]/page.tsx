import React from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getKnowledgeDocumentById, KNOWLEDGE_DOCUMENTS } from "@/lib/knowledge-data";
import { SourceTypeBadge } from "@/components/knowledge/SourceTypeBadge";
import { SourceMetadata } from "@/components/knowledge/SourceMetadata";
import { ArrowLeft, BookOpen, Layers, ShieldCheck, Tag, FileText, User } from "lucide-react";

export function generateStaticParams() {
  return KNOWLEDGE_DOCUMENTS.map((doc) => ({
    documentId: doc.id,
  }));
}

interface PageProps {
  params: {
    documentId: string;
  };
}

export default function DocumentDetailPage({ params }: PageProps) {
  const doc = getKnowledgeDocumentById(params.documentId);

  if (!doc) {
    notFound();
  }

  return (
    <div className="py-8 sm:py-12 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto space-y-6">
      {/* Navigation Breadcrumb */}
      <div>
        <Link
          href="/knowledge-base"
          className="inline-flex items-center space-x-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Return to Knowledge Base Catalog</span>
        </Link>
      </div>

      {/* Main Document Header */}
      <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex items-center space-x-2.5 flex-wrap gap-y-2">
          <SourceTypeBadge sourceType={doc.sourceType} />
          <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
            {doc.id}
          </span>
        </div>

        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
          {doc.title}
        </h1>

        <p className="text-base text-slate-600 leading-relaxed">
          {doc.summary}
        </p>

        <SourceMetadata
          id={doc.id}
          product={doc.product}
          version={doc.version}
          lastUpdated={doc.lastUpdated}
          department={doc.department}
          chunkCount={doc.chunkCount}
        />
      </div>

      {/* Document Content View */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Markdown Content */}
        <div className="lg:col-span-8 bg-white rounded-lg border border-slate-200 p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
              <FileText className="w-4 h-4 text-slate-500" />
              <span>Document Contents</span>
            </h2>
            <span className="text-xs text-slate-500 font-mono">
              Indexed in Qdrant Vector Engine
            </span>
          </div>

          <div className="prose prose-slate max-w-none text-sm leading-relaxed space-y-4 whitespace-pre-wrap text-slate-800">
            {doc.content}
          </div>
        </div>

        {/* Right Column: Provenance & Metadata Panel */}
        <div className="lg:col-span-4 bg-white rounded-lg border border-slate-200 p-5 shadow-xs space-y-4">
          <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2 flex items-center space-x-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Document Provenance</span>
          </h3>

          <div className="space-y-3 text-xs">
            <div>
              <p className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">Product / Category</p>
              <p className="font-semibold text-slate-800 mt-0.5">{doc.product}</p>
            </div>

            <div>
              <p className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">Source Type</p>
              <p className="font-medium text-slate-800 mt-0.5">{doc.sourceType}</p>
            </div>

            <div>
              <p className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">Author / Owner</p>
              <p className="font-medium text-slate-800 mt-0.5">{doc.author} ({doc.department})</p>
            </div>

            <div>
              <p className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">Version / Revision</p>
              <p className="font-mono text-slate-800 mt-0.5">{doc.version}</p>
            </div>

            <div>
              <p className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">Last Updated</p>
              <p className="font-mono text-slate-800 mt-0.5">{doc.lastUpdated}</p>
            </div>

            <div>
              <p className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">Tags</p>
              <div className="flex flex-wrap gap-1 mt-1">
                {doc.tags.map((tag) => (
                  <span
                    key={tag}
                    className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
