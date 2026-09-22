"use client";

import React, { useState, useMemo } from "react";
import {
  KNOWLEDGE_DOCUMENTS,
  ALL_PRODUCTS,
  ALL_SOURCE_TYPES,
  searchKnowledgeBase,
} from "@/lib/knowledge-data";
import { KnowledgeBaseHeader } from "@/components/knowledge/KnowledgeBaseHeader";
import { KnowledgeSearch } from "@/components/knowledge/KnowledgeSearch";
import { SourceList } from "@/components/knowledge/SourceList";

export default function KnowledgeBasePage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [productFilter, setProductFilter] = useState("");
  const [sourceTypeFilter, setSourceTypeFilter] = useState("");

  const filteredDocuments = useMemo(() => {
    return searchKnowledgeBase(searchQuery, productFilter, sourceTypeFilter);
  }, [searchQuery, productFilter, sourceTypeFilter]);

  const handleResetFilters = () => {
    setSearchQuery("");
    setProductFilter("");
    setSourceTypeFilter("");
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
        productsList={ALL_PRODUCTS}
        sourceTypesList={ALL_SOURCE_TYPES}
        onResetFilters={handleResetFilters}
      />

      <SourceList
        documents={filteredDocuments}
        onResetFilters={handleResetFilters}
      />
    </div>
  );
}
