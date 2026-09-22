"use client";

import React from "react";
import { Search, X, Filter } from "lucide-react";
import { SourceType } from "@/lib/knowledge-data";

interface KnowledgeSearchProps {
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  productFilter: string;
  setProductFilter: (p: string) => void;
  sourceTypeFilter: string;
  setSourceTypeFilter: (s: string) => void;
  productsList: string[];
  sourceTypesList: SourceType[];
  onResetFilters: () => void;
}

export function KnowledgeSearch({
  searchQuery,
  setSearchQuery,
  productFilter,
  setProductFilter,
  sourceTypeFilter,
  setSourceTypeFilter,
  productsList,
  sourceTypesList,
  onResetFilters,
}: KnowledgeSearchProps) {
  const hasActiveFilters = Boolean(searchQuery || productFilter || sourceTypeFilter);

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-xs space-y-3">
      <div className="flex flex-col md:flex-row gap-3">
        {/* Search Input */}
        <div className="relative flex-1">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
            <Search className="w-4 h-4" />
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by document title, product, ID (e.g. DOC-2024-881), or tags..."
            className="block w-full pl-9 pr-8 py-2 border border-slate-300 rounded-md text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => setSearchQuery("")}
              className="absolute inset-y-0 right-0 pr-2.5 flex items-center text-slate-400 hover:text-slate-600"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Product Filter */}
        <div className="w-full md:w-52">
          <select
            value={productFilter}
            onChange={(e) => setProductFilter(e.target.value)}
            className="block w-full py-2 px-3 border border-slate-300 bg-white rounded-md text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900"
          >
            <option value="">All Products</option>
            {productsList.map((prod) => (
              <option key={prod} value={prod}>
                {prod}
              </option>
            ))}
          </select>
        </div>

        {/* Source Type Filter */}
        <div className="w-full md:w-56">
          <select
            value={sourceTypeFilter}
            onChange={(e) => setSourceTypeFilter(e.target.value)}
            className="block w-full py-2 px-3 border border-slate-300 bg-white rounded-md text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900"
          >
            <option value="">All Source Types</option>
            {sourceTypesList.map((st) => (
              <option key={st} value={st}>
                {st}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Active Filter Clear Bar */}
      {hasActiveFilters && (
        <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs text-slate-500">
          <span className="flex items-center space-x-1">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <span>Filtering active</span>
          </span>
          <button
            type="button"
            onClick={onResetFilters}
            className="text-slate-600 hover:text-slate-900 font-medium underline flex items-center space-x-1"
          >
            <span>Reset filters</span>
          </button>
        </div>
      )}
    </div>
  );
}
