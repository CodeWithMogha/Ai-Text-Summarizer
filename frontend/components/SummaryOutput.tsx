"use client";

/**
 * SummaryOutput — Displays the AI-generated summary with stats.
 *
 * Features:
 * - Copy to clipboard button
 * - Export as .txt file
 * - Compression ratio display
 * - Token count comparison
 * - Smooth fade-in animation
 */

import { useState } from "react";
import { SummaryResult } from "@/lib/types";

interface SummaryOutputProps {
  result: SummaryResult;
}

export default function SummaryOutput({ result }: SummaryOutputProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(result.summary);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement("textarea");
      textarea.value = result.summary;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleExport = () => {
    const blob = new Blob([result.summary], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `summary_${new Date().toISOString().slice(0, 10)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fade-in space-y-4">
      {/* ── Stats Bar ────────────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard
          label="Original"
          value={`${result.originalLength.toLocaleString()} chars`}
        />
        <StatCard
          label="Summary"
          value={`${result.summaryLength.toLocaleString()} chars`}
        />
        <StatCard
          label="Compression"
          value={`${result.compressionRatio}x`}
          highlight
        />
        <StatCard
          label="Chunks"
          value={`${result.chunksProcessed}`}
        />
      </div>

      {/* ── Extra info (pages, language, etc.) ────────────────── */}
      {result.extraInfo && Object.keys(result.extraInfo).length > 0 && (
        <div className="flex flex-wrap gap-2">
          {Object.entries(result.extraInfo).map(([key, value]) => (
            <span
              key={key}
              className="px-3 py-1 rounded-full text-xs font-medium bg-primary-500/10 text-primary-300 border border-primary-500/20"
            >
              {key}: {value}
            </span>
          ))}
        </div>
      )}

      {/* ── Summary Text ──────────────────────────────────────── */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-slate-200">
            ✨ AI Summary
          </h3>
          <div className="flex gap-2">
            <button
              onClick={handleCopy}
              className="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300
                         bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-primary-500/50"
              id="copy-summary-btn"
            >
              {copied ? "✓ Copied!" : "📋 Copy"}
            </button>
            <button
              onClick={handleExport}
              className="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300
                         bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-primary-500/50"
              id="export-summary-btn"
            >
              💾 Export .txt
            </button>
          </div>
        </div>

        <div className="prose prose-invert max-w-none">
          <p className="text-slate-300 leading-relaxed whitespace-pre-wrap text-[15px]">
            {result.summary}
          </p>
        </div>
      </div>
    </div>
  );
}

// ── Stat Card Sub-Component ──────────────────────────────────
function StatCard({
  label,
  value,
  highlight = false,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div
      className={`rounded-xl p-3 text-center border transition-all duration-300 ${
        highlight
          ? "bg-primary-500/10 border-primary-500/30"
          : "bg-slate-800/50 border-slate-700/50"
      }`}
    >
      <p className="text-xs text-slate-400 mb-1">{label}</p>
      <p
        className={`text-lg font-bold font-mono ${
          highlight ? "text-primary-400" : "text-slate-200"
        }`}
      >
        {value}
      </p>
    </div>
  );
}
