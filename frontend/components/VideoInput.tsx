"use client";

/**
 * VideoInput — URL input + file upload for video summarization.
 *
 * Two modes:
 * 1. Paste a YouTube/Vimeo URL
 * 2. Upload a video/audio file via drag-and-drop
 */

import { useState, useRef, DragEvent } from "react";
import { SummaryLength } from "@/lib/types";

interface VideoInputProps {
  onSubmitURL: (url: string, length: SummaryLength) => void;
  onSubmitFile: (file: File, length: SummaryLength) => void;
  isLoading: boolean;
}

const MAX_VIDEO_SIZE_MB = 100;
const MAX_VIDEO_SIZE_BYTES = MAX_VIDEO_SIZE_MB * 1024 * 1024;

const ALLOWED_EXTENSIONS = [
  ".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv",
  ".mp3", ".wav", ".m4a", ".ogg", ".flac",
];

export default function VideoInput({
  onSubmitURL,
  onSubmitFile,
  isLoading,
}: VideoInputProps) {
  const [videoMode, setVideoMode] = useState<"url" | "upload">("url");
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [length, setLength] = useState<SummaryLength>("medium");
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (f: File): string | null => {
    const ext = "." + f.name.split(".").pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return `Unsupported format: ${ext}. Supported: ${ALLOWED_EXTENSIONS.join(", ")}`;
    }
    if (f.size > MAX_VIDEO_SIZE_BYTES) {
      return `File is ${(f.size / 1024 / 1024).toFixed(0)}MB. Maximum is ${MAX_VIDEO_SIZE_MB}MB.`;
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

  const handleSubmit = () => {
    if (isLoading) return;

    if (videoMode === "url") {
      if (!url.trim().startsWith("http")) {
        setError("Please enter a valid URL starting with http:// or https://");
        return;
      }
      setError(null);
      onSubmitURL(url.trim(), length);
    } else {
      if (!file) {
        setError("Please select a video file.");
        return;
      }
      setError(null);
      onSubmitFile(file, length);
    }
  };

  return (
    <div className="space-y-4 fade-in">
      {/* ── URL / Upload Toggle ─────────────────────────────────── */}
      <div className="flex rounded-xl border border-slate-700 overflow-hidden w-fit">
        <button
          onClick={() => { setVideoMode("url"); setError(null); }}
          className={`px-5 py-2.5 text-sm font-medium transition-all duration-300 ${
            videoMode === "url"
              ? "bg-primary-600 text-white"
              : "bg-slate-800/80 text-slate-400 hover:text-white"
          }`}
        >
          🔗 Paste URL
        </button>
        <button
          onClick={() => { setVideoMode("upload"); setError(null); }}
          className={`px-5 py-2.5 text-sm font-medium transition-all duration-300 ${
            videoMode === "upload"
              ? "bg-primary-600 text-white"
              : "bg-slate-800/80 text-slate-400 hover:text-white"
          }`}
        >
          📁 Upload File
        </button>
      </div>

      {/* ── URL Input ──────────────────────────────────────────── */}
      {videoMode === "url" && (
        <div className="space-y-2">
          <input
            id="video-url-input"
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=..."
            className="input-field"
            disabled={isLoading}
          />
          <p className="text-xs text-slate-500">
            Supports YouTube, Vimeo, and 1000+ other video platforms
          </p>
        </div>
      )}

      {/* ── File Upload ────────────────────────────────────────── */}
      {videoMode === "upload" && (
        <div
          className={`drop-zone ${isDragging ? "dragging" : ""}`}
          onDragOver={(e: DragEvent) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={(e: DragEvent) => { e.preventDefault(); setIsDragging(false); }}
          onDrop={(e: DragEvent) => {
            e.preventDefault();
            setIsDragging(false);
            const f = e.dataTransfer.files[0];
            if (f) handleFile(f);
          }}
          onClick={() => fileInputRef.current?.click()}
          id="video-drop-zone"
        >
          <input
            ref={fileInputRef}
            type="file"
            accept={ALLOWED_EXTENSIONS.join(",")}
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleFile(f);
            }}
            className="hidden"
          />

          {file ? (
            <div className="space-y-2">
              <div className="text-4xl">🎬</div>
              <p className="text-slate-200 font-medium">{file.name}</p>
              <p className="text-slate-400 text-sm">
                {(file.size / 1024 / 1024).toFixed(1)} MB
              </p>
              <button
                onClick={(e) => { e.stopPropagation(); setFile(null); setError(null); }}
                className="text-red-400 text-sm hover:text-red-300"
              >
                ✕ Remove file
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="text-5xl opacity-50">🎥</div>
              <p className="text-slate-300 font-medium">
                Drop your video/audio file here or click to browse
              </p>
              <p className="text-slate-500 text-sm">
                MP4, MKV, AVI, MOV, MP3, WAV • Max {MAX_VIDEO_SIZE_MB}MB
              </p>
            </div>
          )}
        </div>
      )}

      {/* ── Error ──────────────────────────────────────────────── */}
      {error && (
        <p className="text-red-400 text-sm">⚠️ {error}</p>
      )}

      {/* ── Length + Submit ─────────────────────────────────────── */}
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
          disabled={
            isLoading ||
            (videoMode === "url" && !url.trim()) ||
            (videoMode === "upload" && !file)
          }
          className="glow-button flex-1 sm:flex-none"
          id="summarize-video-btn"
        >
          {isLoading ? "Processing Video..." : "✨ Summarize Video"}
        </button>
      </div>

      {/* ── Info note for video ─────────────────────────────────── */}
      <div className="rounded-xl bg-amber-500/5 border border-amber-500/20 p-3">
        <p className="text-amber-300/80 text-xs">
          💡 <strong>Note:</strong> Video processing takes 30-120 seconds depending on
          length. The AI downloads audio, transcribes speech, then summarizes the content.
        </p>
      </div>
    </div>
  );
}
