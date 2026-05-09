/**
 * AI Summarization Platform — TypeScript Type Definitions
 *
 * WHY TYPES MATTER:
 * Without types, you might write: response.sumary (typo!)
 * With types, TypeScript catches this at compile time.
 * Types are your safety net — they catch bugs before users do.
 */

// ── Summary Length Options ────────────────────────────────────
export type SummaryLength = "short" | "medium" | "detailed";

// ── Input Mode for the UI tab switcher ───────────────────────
export type InputMode = "text" | "pdf" | "video";

// ── API Response Types ───────────────────────────────────────

export interface TextSummaryResponse {
  success: boolean;
  summary: string;
  original_length: number;
  summary_length: number;
  original_tokens: number;
  summary_tokens: number;
  compression_ratio: number;
  chunks_processed: number;
}

export interface PDFSummaryResponse {
  success: boolean;
  summary: string;
  original_length: number;
  summary_length: number;
  pages_processed: number;
  pages_with_text: number;
  original_tokens: number;
  summary_tokens: number;
  compression_ratio: number;
  chunks_processed: number;
}

export interface VideoSummaryResponse {
  success: boolean;
  summary: string;
  detected_language: string;
  transcript_length: number;
  summary_length: number;
  original_tokens: number;
  summary_tokens: number;
  compression_ratio: number;
  chunks_processed: number;
  source_url?: string;
  filename?: string;
  transcript?: string;
  segments?: TranscriptSegment[];
}

export interface TranscriptSegment {
  start: number;
  end: number;
  text: string;
}

// ── API Error Response ───────────────────────────────────────

export interface APIError {
  error: string;
  message: string;
}

export interface APIErrorResponse {
  detail: APIError;
}

// ── Component Props ──────────────────────────────────────────

export interface SummaryResult {
  summary: string;
  originalLength: number;
  summaryLength: number;
  compressionRatio: number;
  chunksProcessed: number;
  extraInfo?: Record<string, string | number>;
}
