"use client";

/**
 * PDFUpload — Drag-and-drop PDF file upload with preview.
 */

import { useState, useRef, DragEvent } from "react";
import { SummaryLength } from "@/lib/types";

interface PDFUploadProps {
  onSubmit: (file: File, length: SummaryLength) => void;
  isLoading: boolean;
}

const MAX_SIZE_MB = 10;
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;

export default function PDFUpload({ onSubmit, isLoading }: PDFUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [length, setLength] = useState<SummaryLength>("medium");
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (f: File): string | null => {
    if (!f.name.toLowerCase().endsWith(".pdf")) {
      return "Please upload a PDF file (.pdf)";
    }
    if (f.size > MAX_SIZE_BYTES) {
      return `File is ${(f.size / 1024 / 1024).toFixed(1)}MB. Maximum is ${MAX_SIZE_MB}MB.`;
    }
    if (f.size === 0) {
      return "File is empty.";
    }
    return null;
  };

  const handleFile = (f: File) => {
    const validationError = validateFile(f);
    if (validationError) {
      setError(validationError);
      setFile(null);
      return;
    }
    setError(null);
    setFile(f);
  };

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) handleFile(droppedFile);
  };

  const handleSubmit = () => {
    if (file && !isLoading) {
      onSubmit(file, length);
    }
  };

  return (
    <div className="space-y-4 fade-in">
      {/* ── Drop Zone ──────────────────────────────────────────── */}
      <div
        className={`drop-zone ${isDragging ? "dragging" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        id="pdf-drop-zone"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFile(f);
          }}
          className="hidden"
          id="pdf-file-input"
        />

        {file ? (
          <div className="space-y-2">
            <div className="text-4xl">📄</div>
            <p className="text-slate-200 font-medium">{file.name}</p>
            <p className="text-slate-400 text-sm">
              {(file.size / 1024 / 1024).toFixed(2)} MB
            </p>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setFile(null);
                setError(null);
              }}
              className="text-red-400 text-sm hover:text-red-300 transition-colors"
            >
              ✕ Remove file
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="text-5xl opacity-50">📁</div>
            <p className="text-slate-300 font-medium">
              Drop your PDF here or click to browse
            </p>
            <p className="text-slate-500 text-sm">
              Maximum file size: {MAX_SIZE_MB}MB
            </p>
          </div>
        )}
      </div>

      {/* ── Error Message ──────────────────────────────────────── */}
      {error && (
        <p className="text-red-400 text-sm flex items-center gap-2">
          <span>⚠️</span> {error}
        </p>
      )}

      {/* ── Length Selector + Submit ────────────────────────────── */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
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
            >
              {len}
            </button>
          ))}
        </div>

        <button
          onClick={handleSubmit}
          disabled={!file || isLoading}
          className="glow-button flex-1 sm:flex-none"
          id="summarize-pdf-btn"
        >
          {isLoading ? "Processing PDF..." : "✨ Summarize PDF"}
        </button>
      </div>
    </div>
  );
}
