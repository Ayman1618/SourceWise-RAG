"use client";

import React from "react";
import { Search, Loader2, ArrowRight, Sparkles } from "lucide-react";

export const DEMO_SAMPLE_QUESTIONS = [
  "How do I troubleshoot login failures?",
  "What are the API rate limits?",
  "How does authentication work?",
];

interface QuestionInputProps {
  question: string;
  setQuestion: (val: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  isLoading: boolean;
}

export function QuestionInput({
  question,
  setQuestion,
  onSubmit,
  isLoading,
}: QuestionInputProps) {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      if (question.trim() && !isLoading) {
        onSubmit(e);
      }
    }
  };

  const handleSampleClick = (sampleQuery: string) => {
    setQuestion(sampleQuery);
  };

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 sm:p-6 shadow-sm">
      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="question-input"
            className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-2 flex items-center justify-between"
          >
            <span className="flex items-center space-x-1.5">
              <Search className="w-4 h-4 text-slate-500" />
              <span>Enterprise Knowledge Query</span>
            </span>
            <span className="text-slate-400 font-normal normal-case text-xs hidden sm:inline">
              Press Cmd/Ctrl + Enter to submit
            </span>
          </label>
          <div className="relative">
            <textarea
              id="question-input"
              rows={3}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              placeholder="Ask a question about your internal documentation..."
              className="block w-full p-3.5 border border-slate-300 rounded-md text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900 text-sm leading-relaxed disabled:bg-slate-50 disabled:text-slate-500 transition-colors"
            />
          </div>
        </div>

        {/* Demo Usability: Suggested Prompts matching sample documents */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="text-slate-500 font-medium flex items-center space-x-1">
            <Sparkles className="w-3.5 h-3.5 text-brand-900" />
            <span>Suggested Demo Prompts:</span>
          </span>
          {DEMO_SAMPLE_QUESTIONS.map((sample, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleSampleClick(sample)}
              disabled={isLoading}
              className="inline-flex items-center px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-800 font-medium transition-colors border border-slate-200 disabled:opacity-50"
            >
              <span>{sample}</span>
            </button>
          ))}
        </div>

        {/* Submit Action Row */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-100 flex-wrap gap-2">
          <span className="text-xs text-slate-500">
            Queries internal knowledge base via <code className="font-mono text-slate-700">POST /api/v1/query</code>
          </span>
          <button
            type="submit"
            disabled={!question.trim() || isLoading}
            className="inline-flex items-center justify-center space-x-2 px-5 py-2.5 rounded-md bg-brand-900 hover:bg-brand-800 disabled:bg-slate-200 disabled:text-slate-400 text-white text-sm font-medium transition-colors shadow-sm focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                <span>Processing RAG Query...</span>
              </>
            ) : (
              <>
                <span>Ask SourceWise</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
