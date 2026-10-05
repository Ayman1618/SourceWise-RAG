"use client";

/**
 * SourceWise RAG Knowledge Base Catalog Page Component
 * Renders enterprise document catalog, search, and multi-criteria filters (PR 29).
 */

import React, { useState, useMemo } from "react";
import {
  KNOWLEDGE_DOCUMENTS,
  ALL_PRODUCTS,
  ALL_SOURCE_TYPES,
  ALL_DEPARTMENTS,
  ALL_VERSIONS,
  searchKnowledgeBase,
} from "@/lib/knowledge-data";
import { KnowledgeBaseHeader } from "@/components/knowledge/KnowledgeBaseHeader";
import { KnowledgeSearch } from "@/components/knowledge/KnowledgeSearch";
import { SourceList } from "@/components/knowledge/SourceList";

export default function KnowledgeBasePage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [productFilter, setProductFilter] = useState("");
  const [sourceTypeFilter, setSourceTypeFilter] = useState("");
  const [departmentFilter, setDepartmentFilter] = useState("");
  const [versionFilter, setVersionFilter] = useState("");

  const filteredDocuments = useMemo(() => {
    return searchKnowledgeBase(
      searchQuery,
      productFilter,
      sourceTypeFilter,
      departmentFilter,
      versionFilter
    );
  }, [searchQuery, productFilter, sourceTypeFilter, departmentFilter, versionFilter]);

  const handleResetFilters = () => {
    setSearchQuery("");
    setProductFilter("");
    setSourceTypeFilter("");
    setDepartmentFilter("");
    setVersionFilter("");
  };

  return (
    <div className="py-8 sm:py-12 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto space-y-6">
      <KnowledgeBaseHeader totalDocs={KNOWLEDGE_DOCUMENTS.length} />

      <KnowledgeSearch
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        productFilter={productFilter}
        setProductFilter={setProductFilter}
        sourceTypeFilter={sourceTypeFilter}
        setSourceTypeFilter={setSourceTypeFilter}
        departmentFilter={departmentFilter}
        setDepartmentFilter={setDepartmentFilter}
        versionFilter={versionFilter}
        setVersionFilter={setVersionFilter}
        productsList={ALL_PRODUCTS}
        sourceTypesList={ALL_SOURCE_TYPES}
        departmentsList={ALL_DEPARTMENTS}
        versionsList={ALL_VERSIONS}
        onResetFilters={handleResetFilters}
      />

      <SourceList
        documents={filteredDocuments}
        onResetFilters={handleResetFilters}
      />
    </div>
  );
}
