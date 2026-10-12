"use client";

import React, { useState, useMemo } from "react";
import ReactMarkdown from "react-markdown";
import { Citation, EvidenceStatus } from "@/lib/types/rag";
import { ShieldCheck, Copy, Check, Sparkles, AlertCircle } from "lucide-react";

interface AnswerPanelProps {
  answer: string;
  citations: Citation[];
  confidenceScore?: number | null;
  evidenceStatus?: EvidenceStatus;
  onSelectCitation: (citationId: string) => void;
}

/**
 * Preprocesses markdown text so that citation brackets like:
 * [sample-login-troubleshooting#chunk_0], [cite_1], or [1]
 * are turned into markdown citation links: [cite_1](citation:cite_1).
 */
function preprocessCitations(text: string, citations: Citation[]): string {
  if (!text) return "";

  // Match bracketed citation references that are NOT part of an existing markdown link [text](url)
  return text.replace(/\[([^\]]+)\](?!\()/g, (match, inner) => {
    // If it's a list like "chunk_0, chunk_1"
    const parts = inner.split(/,\s*/);
    const converted = parts.map((rawPart: string) => {
      const part = rawPart.trim();

      // 1. Direct match on citation_id (e.g. cite_1, 1)
      let found = citations.find(
        (c) => c.citation_id === part || c.citation_id === `cite_${part}`
      );

      // 2. Match on chunk_id (e.g. sample-login-troubleshooting#chunk_0)
      if (!found) {
        found = citations.find(
          (c) => c.chunk_id === part || c.chunk_id.includes(part) || part.includes(c.chunk_id)
        );
      }

      if (found) {
        return `[${found.citation_id}](citation:${found.citation_id})`;
      }

      // 3. Fallback for numeric or cite_ format even if citations array is empty
      if (/^\d+$/.test(part) || /^cite_\d+$/.test(part)) {
        return `[${part}](citation:${part})`;
      }

      // 4. Fallback for raw chunk tags (e.g. #chunk_0)
      if (part.includes("#chunk_") || part.includes("chunk_")) {
        const shortLabel = part.split("#").pop() || part;
        return `[${shortLabel}](citation:${part})`;
      }

      return null;
    });

    if (converted.every((item: string | null) => item !== null)) {
      return converted.join(" ");
    }

    return match;
  });
}

export function AnswerPanel({
  answer,
  citations,
  confidenceScore,
  evidenceStatus = "sufficient",
  onSelectCitation,
}: AnswerPanelProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const processedContent = useMemo(() => {
    return preprocessCitations(answer, citations);
  }, [answer, citations]);

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 sm:p-6 shadow-sm space-y-4">
      {/* Panel Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3 flex-wrap gap-2">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="w-5 h-5 text-brand-900" />
          <h3 className="text-base font-bold text-slate-900 tracking-tight">
            Answer
          </h3>
        </div>

        <div className="flex items-center space-x-2 flex-wrap gap-1.5">
          {confidenceScore !== undefined && confidenceScore !== null && (
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
              Confidence: {Math.round(confidenceScore * 100)}%
            </span>
          )}

          <span
            className={`inline-flex items-center space-x-1 text-xs font-medium px-2.5 py-0.5 rounded border ${
              evidenceStatus === "sufficient"
                ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                : "bg-amber-50 text-amber-700 border-amber-200"
            }`}
          >
            {evidenceStatus === "sufficient" ? (
              <>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>Grounded Answer</span>
              </>
            ) : (
              <>
                <AlertCircle className="w-3 h-3 text-amber-600" />
                <span>Status: {evidenceStatus}</span>
              </>
            )}
          </span>

          <button
            type="button"
            onClick={handleCopy}
            className="p-1.5 rounded text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            title="Copy answer text"
          >
            {copied ? (
              <Check className="w-4 h-4 text-emerald-600" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Formatted Markdown Answer Content */}
      <div className="text-slate-800 text-sm sm:text-base leading-relaxed font-normal">
        <ReactMarkdown
          components={{
            p: ({ children }) => (
              <p className="mb-3 leading-relaxed text-slate-800 last:mb-0">
                {children}
              </p>
            ),
            strong: ({ children }) => (
              <strong className="font-semibold text-slate-900">
                {children}
              </strong>
            ),
            em: ({ children }) => (
              <em className="italic text-slate-800">{children}</em>
            ),
            ul: ({ children }) => (
              <ul className="list-disc pl-5 my-2.5 space-y-1.5 text-slate-800">
                {children}
              </ul>
            ),
            ol: ({ children }) => (
              <ol className="list-decimal pl-5 my-2.5 space-y-1.5 text-slate-800">
                {children}
              </ol>
            ),
            li: ({ children }) => (
              <li className="leading-relaxed">{children}</li>
            ),
            blockquote: ({ children }) => (
              <blockquote className="border-l-4 border-slate-300 pl-3 italic my-2.5 text-slate-700">
                {children}
              </blockquote>
            ),
            code: ({ className, children }) => {
              const isBlock = className || (typeof children === "string" && children.includes("\n"));
              if (isBlock) {
                return (
                  <pre className="bg-slate-900 text-slate-100 p-3 rounded-md text-xs font-mono overflow-x-auto my-3">
                    <code>{children}</code>
                  </pre>
                );
              }
              return (
                <code className="bg-slate-100 text-slate-800 px-1.5 py-0.5 rounded font-mono text-xs border border-slate-200">
                  {children}
                </code>
              );
            },
            a: ({ href, children }) => {
              if (href?.startsWith("citation:")) {
                const citationId = href.replace("citation:", "");
                const exists = citations.some(
                  (c) =>
                    c.citation_id === citationId ||
                    c.citation_id === `cite_${citationId}` ||
                    c.chunk_id === citationId
                );

                return (
                  <button
                    type="button"
                    onClick={() => onSelectCitation(citationId)}
                    title={`View Supporting Evidence [${citationId}]`}
                    className={`inline-flex items-center px-1.5 py-0.2 mx-0.5 text-xs font-mono font-bold rounded transition-colors focus:outline-none focus:ring-2 focus:ring-brand-900 focus:ring-offset-1 align-baseline ${
                      exists
                        ? "bg-brand-900 hover:bg-brand-800 text-white shadow-2xs"
                        : "bg-slate-800 hover:bg-slate-700 text-white"
                    }`}
                  >
                    [{children}]
                  </button>
                );
              }

              return (
                <a
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-brand-700 hover:text-brand-900 underline font-medium transition-colors"
                >
                  {children}
                </a>
              );
            },
          }}
        >
          {processedContent}
        </ReactMarkdown>
      </div>

      {/* Footer Info */}
      <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
        <span className="flex items-center space-x-1">
          <Sparkles className="w-3.5 h-3.5 text-slate-400" />
          <span>Click citation tags like [1] to highlight supporting evidence</span>
        </span>
      </div>
    </div>
  );
}
