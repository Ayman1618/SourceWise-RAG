import React from "react";
import Link from "next/link";
import { KnowledgeDocument } from "@/lib/knowledge-data";
import { SourceTypeBadge } from "./SourceTypeBadge";
import { SourceMetadata } from "./SourceMetadata";
import { ArrowRight, FileText } from "lucide-react";

interface SourceListItemProps {
  document: KnowledgeDocument;
}

export function SourceListItem({ document }: SourceListItemProps) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 sm:p-5 hover:border-slate-300 transition-all duration-200 shadow-xs group">
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        {/* Content Details */}
        <div className="space-y-2.5 flex-1">
          <div className="flex items-center space-x-2.5 flex-wrap gap-y-1">
            <SourceTypeBadge sourceType={document.sourceType} />
            <Link
              href={`/knowledge-base/${document.id}`}
              className="text-base font-semibold text-slate-900 group-hover:text-brand-900 transition-colors leading-snug"
            >
              {document.title}
            </Link>
          </div>

          <p className="text-sm text-slate-600 leading-relaxed line-clamp-2">
            {document.summary}
          </p>

          <SourceMetadata
            id={document.id}
            product={document.product}
            version={document.version}
            lastUpdated={document.lastUpdated}
            department={document.department}
            chunkCount={document.chunkCount}
          />
        </div>

        {/* Action Button */}
        <div className="shrink-0 self-end md:self-start pt-2 md:pt-0">
          <Link
            href={`/knowledge-base/${document.id}`}
            className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded bg-slate-900 text-white hover:bg-brand-900 text-xs font-medium transition-colors shadow-xs"
          >
            <span>Inspect Source</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>
    </div>
  );
}
