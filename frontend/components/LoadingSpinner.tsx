"use client";

/**
 * LoadingSpinner — Animated loading indicator with progress messages.
 *
 * WHY PROGRESS MESSAGES?
 * When a video takes 60 seconds to process, showing "Loading..." the
 * entire time makes users think it's broken. Showing step-by-step
 * progress ("Downloading audio...", "Transcribing...") keeps them
 * engaged and confident it's working.
 */

import { useEffect, useState } from "react";

interface LoadingSpinnerProps {
  mode: "text" | "pdf" | "video";
}

const PROGRESS_MESSAGES: Record<string, string[]> = {
  text: [
    "Analyzing your text...",
    "Identifying key themes...",
    "Generating summary...",
    "Almost there...",
  ],
  pdf: [
    "Reading PDF pages...",
    "Extracting text content...",
    "Analyzing document structure...",
    "Generating summary...",
    "Finalizing...",
  ],
  video: [
    "Downloading audio...",
    "Converting audio format...",
    "Transcribing speech with AI...",
    "Cleaning transcript...",
    "Analyzing content...",
    "Generating summary...",
    "Almost done...",
  ],
};

export default function LoadingSpinner({ mode }: LoadingSpinnerProps) {
  const [messageIndex, setMessageIndex] = useState(0);
  const messages = PROGRESS_MESSAGES[mode] || PROGRESS_MESSAGES.text;

  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((prev) =>
        prev < messages.length - 1 ? prev + 1 : prev
      );
    }, 3000); // Change message every 3 seconds

    return () => clearInterval(interval);
  }, [messages.length]);

  return (
    <div className="flex flex-col items-center justify-center py-16 fade-in">
      {/* Animated spinner */}
      <div className="relative w-16 h-16 mb-6">
        {/* Outer ring */}
        <div className="absolute inset-0 border-4 border-primary-500/20 rounded-full" />
        {/* Spinning arc */}
        <div className="absolute inset-0 border-4 border-transparent border-t-primary-500 rounded-full animate-spin" />
        {/* Inner glow */}
        <div className="absolute inset-2 bg-primary-500/10 rounded-full animate-pulse" />
      </div>

      {/* Progress message */}
      <p className="text-base text-slate-300 font-medium animate-pulse">
        {messages[messageIndex]}
      </p>

      {/* Step counter */}
      <div className="flex items-center gap-2 mt-4">
        {messages.map((_, i) => (
          <div
            key={i}
            className={`w-2 h-2 rounded-full transition-all duration-500 ${
              i <= messageIndex
                ? "bg-primary-500 scale-100"
                : "bg-slate-700 scale-75"
            }`}
          />
        ))}
      </div>

      <p className="text-sm text-slate-500 mt-4">
        Step {messageIndex + 1} of {messages.length}
      </p>
    </div>
  );
}
