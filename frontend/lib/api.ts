/**
 * AI Summarization Platform — API Client
 */

import {
  TextSummaryResponse,
  PDFSummaryResponse,
  VideoSummaryResponse,
  SummaryLength,
  APIErrorResponse,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = "An unexpected error occurred. Please try again.";

    try {
      const errorData: APIErrorResponse = await response.json();
      if (errorData.detail?.message) {
        errorMessage = errorData.detail.message;
      }
    } catch {
      if (response.status === 413) {
        errorMessage = "File is too large. Please try a smaller file.";
      } else if (response.status === 422) {
        errorMessage = "Invalid input. Please check your data and try again.";
      } else if (response.status === 429) {
        errorMessage = "Too many requests. Please wait a moment and try again.";
      } else if (response.status === 500) {
        errorMessage = "Server error. Please try again later.";
      }
    }

    throw new Error(errorMessage);
  }

  return response.json();
}

export async function summarizeText(
  text: string,
  length: SummaryLength = "medium",
  style: string = "paragraph",
  language: string = "english"
): Promise<TextSummaryResponse> {
  const response = await fetch(`${API_URL}/api/summarize/text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, length, style, language }),
  });

  return handleResponse<TextSummaryResponse>(response);
}

export async function summarizePDF(
  file: File,
  length: SummaryLength = "medium",
  style: string = "paragraph",
  language: string = "english"
): Promise<PDFSummaryResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("length", length);
  formData.append("style", style);
  formData.append("language", language);

  const response = await fetch(`${API_URL}/api/summarize/pdf`, {
    method: "POST",
    body: formData,
  });

  return handleResponse<PDFSummaryResponse>(response);
}

export async function summarizeVideoURL(
  url: string,
  length: SummaryLength = "medium",
  style: string = "paragraph",
  language: string = "english",
  includeTranscript: boolean = false
): Promise<VideoSummaryResponse> {
  const response = await fetch(`${API_URL}/api/summarize/video/url`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      url,
      length,
      style,
      language,
      include_transcript: includeTranscript,
    }),
  });

  return handleResponse<VideoSummaryResponse>(response);
}

export async function summarizeVideoUpload(
  file: File,
  length: SummaryLength = "medium",
  style: string = "paragraph",
  language: string = "english",
  includeTranscript: boolean = false
): Promise<VideoSummaryResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("length", length);
  formData.append("style", style);
  formData.append("language", language);
  formData.append("include_transcript", String(includeTranscript));

  const response = await fetch(`${API_URL}/api/summarize/video/upload`, {
    method: "POST",
    body: formData,
  });

  return handleResponse<VideoSummaryResponse>(response);
}
