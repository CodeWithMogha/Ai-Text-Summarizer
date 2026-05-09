import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Summarizer — Text, PDF & Video Summarization",
  description:
    "Summarize any text, PDF document, or video in seconds using AI. Powered by Google Gemini and OpenAI Whisper.",
  keywords: [
    "AI summarizer",
    "text summarization",
    "PDF summary",
    "video summary",
    "YouTube summary",
    "OpenAI",
    "GPT",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased">{children}</body>
    </html>
  );
}
