import React from "react";
import { SourceType } from "@/lib/knowledge-data";
import { FileText, Wrench, Code2, BookOpen, ShieldAlert } from "lucide-react";

interface SourceTypeBadgeProps {
  sourceType: SourceType;
}

export function SourceTypeBadge({ sourceType }: SourceTypeBadgeProps) {
  const getBadgeConfig = (type: SourceType) => {
    switch (type) {
      case "Support Documentation":
        return {
          icon: FileText,
          style: "bg-blue-50 text-blue-700 border-blue-200",
        };
      case "Engineering Specification":
        return {
          icon: Code2,
          style: "bg-purple-50 text-purple-700 border-purple-200",
        };
      case "Developer Reference":
        return {
          icon: BookOpen,
          style: "bg-slate-100 text-slate-800 border-slate-300",
        };
      case "Operations Runbook":
        return {
          icon: Wrench,
          style: "bg-amber-50 text-amber-800 border-amber-200",
        };
      case "Regulatory Standard":
        return {
          icon: ShieldAlert,
          style: "bg-emerald-50 text-emerald-800 border-emerald-200",
        };
      default:
        return {
          icon: FileText,
          style: "bg-slate-100 text-slate-700 border-slate-200",
        };
    }
  };

  const config = getBadgeConfig(sourceType);
  const Icon = config.icon;

  return (
    <span
      className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded text-xs font-medium border ${config.style}`}
    >
      <Icon className="w-3 h-3 shrink-0" />
      <span>{sourceType}</span>
    </span>
  );
}
