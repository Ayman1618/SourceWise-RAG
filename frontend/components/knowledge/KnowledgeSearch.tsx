"use client";

import React from "react";
import { Search, X, Filter, RotateCcw } from "lucide-react";
import { SourceType } from "@/lib/knowledge-data";

interface KnowledgeSearchProps {
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  productFilter: string;
  setProductFilter: (p: string) => void;
  sourceTypeFilter: string;
  setSourceTypeFilter: (s: string) => void;
  departmentFilter: string;
  setDepartmentFilter: (d: string) => void;
  versionFilter: string;
  setVersionFilter: (v: string) => void;
  productsList: string[];
  sourceTypesList: SourceType[];
  departmentsList: string[];
  versionsList: string[];
  onResetFilters: () => void;
}

export function KnowledgeSearch({
  searchQuery,
  setSearchQuery,
  productFilter,
  setProductFilter,
  sourceTypeFilter,
  setSourceTypeFilter,
  departmentFilter,
  setDepartmentFilter,
  versionFilter,
  setVersionFilter,
  productsList,
  sourceTypesList,
  departmentsList,
  versionsList,
  onResetFilters,
}: KnowledgeSearchProps) {
  const hasActiveFilters = Boolean(
    searchQuery || productFilter || sourceTypeFilter || departmentFilter || versionFilter
  );

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-xs space-y-4">
      {/* Search Input Row */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
          <Search className="w-4 h-4" />
        </div>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search by document title, product, department, ID (e.g. DOC-2024-881), or tags..."
          className="block w-full pl-10 pr-9 py-2.5 border border-slate-300 rounded-md text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900 shadow-2xs"
        />
        {searchQuery && (
          <button
            type="button"
            onClick={() => setSearchQuery("")}
            className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 transition-colors"
            title="Clear search"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Filters Grid: Product, Source Type, Department, Version */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Product Filter */}
        <div>
          <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
            Product
          </label>
          <select
            value={productFilter}
            onChange={(e) => setProductFilter(e.target.value)}
            className="block w-full py-1.5 px-2.5 border border-slate-300 bg-white rounded-md text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900"
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
        <div>
          <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
            Source Type
          </label>
          <select
            value={sourceTypeFilter}
            onChange={(e) => setSourceTypeFilter(e.target.value)}
            className="block w-full py-1.5 px-2.5 border border-slate-300 bg-white rounded-md text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900"
          >
            <option value="">All Source Types</option>
            {sourceTypesList.map((st) => (
              <option key={st} value={st}>
                {st}
              </option>
            ))}
          </select>
        </div>

        {/* Department Filter */}
        <div>
          <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
            Department
          </label>
          <select
            value={departmentFilter}
            onChange={(e) => setDepartmentFilter(e.target.value)}
            className="block w-full py-1.5 px-2.5 border border-slate-300 bg-white rounded-md text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900"
          >
            <option value="">All Departments</option>
            {departmentsList.map((dept) => (
              <option key={dept} value={dept}>
                {dept}
              </option>
            ))}
          </select>
        </div>

        {/* Version Filter */}
        <div>
          <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
            Version
          </label>
          <select
            value={versionFilter}
            onChange={(e) => setVersionFilter(e.target.value)}
            className="block w-full py-1.5 px-2.5 border border-slate-300 bg-white rounded-md text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900"
          >
            <option value="">All Versions</option>
            {versionsList.map((ver) => (
              <option key={ver} value={ver}>
                {ver}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Active Filters Summary Bar */}
      {hasActiveFilters && (
        <div className="flex items-center justify-between pt-2.5 border-t border-slate-100 text-xs text-slate-600">
          <div className="flex items-center space-x-2 flex-wrap gap-y-1">
            <span className="flex items-center space-x-1 font-medium text-slate-700">
              <Filter className="w-3.5 h-3.5 text-slate-500" />
              <span>Active filters:</span>
            </span>
            {searchQuery && (
              <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-mono text-[11px] border border-slate-200">
                &quot;{searchQuery}&quot;
              </span>
            )}
            {productFilter && (
              <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium text-[11px] border border-slate-200">
                Product: {productFilter}
              </span>
            )}
            {sourceTypeFilter && (
              <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium text-[11px] border border-slate-200">
                Type: {sourceTypeFilter}
              </span>
            )}
            {departmentFilter && (
              <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium text-[11px] border border-slate-200">
                Dept: {departmentFilter}
              </span>
            )}
            {versionFilter && (
              <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-mono text-[11px] border border-slate-200">
                Ver: {versionFilter}
              </span>
            )}
          </div>
          <button
            type="button"
            onClick={onResetFilters}
            className="text-slate-600 hover:text-slate-900 font-medium flex items-center space-x-1 underline transition-colors shrink-0 ml-2"
          >
            <RotateCcw className="w-3 h-3" />
            <span>Reset filters</span>
          </button>
        </div>
      )}
    </div>
  );
}
