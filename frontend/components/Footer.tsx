import React from "react";

export function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white py-8 mt-auto">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
        <div>
          <p className="font-medium text-slate-700">SourceWise RAG — Retrieve. Ground. Verify.</p>
          <p className="mt-1">Enterprise Grounded Intelligence Architecture.</p>
        </div>
        <div className="text-right sm:text-right">
          <p>Frontend Application Foundation — PR 3</p>
          <p className="mt-1">© {new Date().getFullYear()} SourceWise RAG Team</p>
        </div>
      </div>
    </footer>
  );
}
