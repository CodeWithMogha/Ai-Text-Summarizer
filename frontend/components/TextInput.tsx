"use client";

/**
 * TextInput — Text area for raw text input with character count.
 */

import { useState } from "react";
import { SummaryLength } from "@/lib/types";

interface TextInputProps {
  onSubmit: (text: string, length: SummaryLength) => void;
  isLoading: boolean;
}

const MAX_CHARS = 100000;

export default function TextInput({ onSubmit, isLoading }: TextInputProps) {
  const [text, setText] = useState("");
  const [length, setLength] = useState<SummaryLength>("medium");

  const charCount = text.length;
  const isOverLimit = charCount > MAX_CHARS;
  const isEmpty = charCount < 10;

  const handleSubmit = () => {
    if (!isEmpty && !isOverLimit && !isLoading) {
      onSubmit(text, length);
    }
  };

  return (
    <div className="space-y-4 fade-in">
      {/* ── Text Area ──────────────────────────────────────────── */}
      <div className="relative">
        <textarea
          id="text-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste or type your text here... (minimum 10 characters)"
          className="input-field min-h-[240px] resize-y font-sans"
          disabled={isLoading}
        />

        {/* Character counter */}
        <div className="absolute bottom-3 right-4 flex items-center gap-2">
          <span
            className={`text-xs font-mono ${
              isOverLimit
                ? "text-red-400"
                : charCount > MAX_CHARS * 0.9
                ? "text-yellow-400"
                : "text-slate-500"
            }`}
          >
            {charCount.toLocaleString()} / {MAX_CHARS.toLocaleString()}
          </span>
        </div>
      </div>

      {/* ── Length Selector + Submit ────────────────────────────── */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
        {/* Summary length toggle */}
        <div className="flex rounded-xl border border-slate-700 overflow-hidden">
          {(["short", "medium", "detailed"] as SummaryLength[]).map((len) => (
            <button
              key={len}
              onClick={() => setLength(len)}
              className={`px-4 py-2.5 text-sm font-medium transition-all duration-300 capitalize ${
                length === len
                  ? "bg-primary-600 text-white"
                  : "bg-slate-800/80 text-slate-400 hover:text-white hover:bg-slate-700"
              }`}
              id={`length-${len}-btn`}
            >
              {len}
            </button>
          ))}
        </div>

        {/* Submit button */}
        <button
          onClick={handleSubmit}
          disabled={isEmpty || isOverLimit || isLoading}
          className="glow-button flex-1 sm:flex-none"
          id="summarize-text-btn"
        >
          {isLoading ? "Summarizing..." : "✨ Summarize Text"}
        </button>
      </div>

      {/* ── Validation messages ─────────────────────────────────── */}
      {isOverLimit && (
        <p className="text-red-400 text-sm">
          ⚠️ Text exceeds {MAX_CHARS.toLocaleString()} character limit.
          Please shorten your text.
        </p>
      )}
    </div>
  );
}
