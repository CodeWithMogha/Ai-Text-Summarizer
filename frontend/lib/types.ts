/**
 * AI Summarization Platform — TypeScript Type Definitions
 */

export type SummaryLength = "short" | "medium" | "detailed";

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

export interface APIError {
  error: string;
  message: string;
}

export interface APIErrorResponse {
  detail: APIError;
}
