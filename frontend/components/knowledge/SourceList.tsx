import React from "react";
import { KnowledgeDocument } from "@/lib/knowledge-data";
import { SourceListItem } from "./SourceListItem";
import { Info, SearchX } from "lucide-react";

interface SourceListProps {
  documents: KnowledgeDocument[];
  onResetFilters?: () => void;
}

export function SourceList({ documents, onResetFilters }: SourceListProps) {
  if (documents.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-8 text-center space-y-3 shadow-xs">
        <SearchX className="w-8 h-8 text-slate-400 mx-auto" />
        <h3 className="text-base font-semibold text-slate-900">
          No knowledge sources match your search
        </h3>
        <p className="text-sm text-slate-600 max-w-md mx-auto">
          Try searching for different keywords, products, or resetting your filter selections.
        </p>
        {onResetFilters && (
          <div className="pt-2">
            <button
              type="button"
              onClick={onResetFilters}
              className="inline-flex items-center space-x-1 px-4 py-2 rounded bg-slate-900 text-white text-xs font-medium hover:bg-slate-800 transition-colors shadow-xs"
            >
              <span>Reset Search Filters</span>
            </button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between text-xs text-slate-500 px-1">
        <span>Showing {documents.length} knowledge sources</span>
        <span>Repository Status: Active Index</span>
      </div>

      <div className="space-y-3">
        {documents.map((doc) => (
          <SourceListItem key={doc.id} document={doc} />
        ))}
      </div>
    </div>
  );
}
