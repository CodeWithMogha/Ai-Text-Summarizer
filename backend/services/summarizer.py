"""
AI Summarization Platform — OpenAI GPT Summarizer Service

WHY THIS IS THE HEART OF THE APP:
Every pipeline (text, PDF, video) ends here. This service takes raw text
and produces a clean summary using GPT-3.5-turbo.

THE MAP-REDUCE PATTERN:
Imagine you have 100 pages to summarize. You can't hand all 100 to GPT at once
(token limit). So:
  1. MAP: Summarize each chunk independently → 10 mini-summaries
  2. REDUCE: Combine all mini-summaries → 1 final summary

This is the same pattern Google uses for processing petabytes of data,
just applied to text summarization.
"""

import os
import google.generativeai as genai
from typing import Optional
from utils.chunker import chunk_text, count_tokens
from utils.logger import logger


# Flag to check if initialized
_gemini_initialized = False


def init_gemini() -> bool:
    """Initialize Gemini API and return True if successful."""
    global _gemini_initialized
    if not _gemini_initialized:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key.startswith("sk-your"):
            return False
        genai.configure(api_key=api_key)
        _gemini_initialized = True
        logger.info("Gemini API initialized")
    return _gemini_initialized


# Summary length presets — the user picks one from the frontend
SUMMARY_PROMPTS = {
    "short": {
        "paragraph": "Summarize the following text in 2-3 concise sentences. Focus only on the single most important takeaway. Do not use bullet points.",
        "bullets": "Summarize the following text into exactly 2 or 3 concise bullet points. Focus only on the single most important takeaway."
    },
    "medium": {
        "paragraph": "Summarize the following text in a clear, well-structured paragraph. Cover the main points and key details. Aim for about 150 words. Do not use bullet points.",
        "bullets": "Summarize the following text into 4 to 6 clear bullet points. Cover the main points and key details. Aim for about 150 words total."
    },
    "detailed": {
        "paragraph": "Provide a detailed summary of the following text in 3 to 4 comprehensive paragraphs. Cover all key topics, important details, examples, and conclusions. Aim for about 300 words. Do not use bullet points.",
        "bullets": "Provide a detailed summary of the following text using bullet points. Use nested bullet points if necessary. Include all key topics, important details, examples, and conclusions. Aim for about 300 words."
    },
}


async def summarize_text(
    text: str,
    length: str = "medium",
    style: str = "paragraph",
    language: str = "english"
) -> dict:
    """
    Summarize text using Gemini 1.5 Flash with map-reduce for long texts.
    
    Args:
        text: The raw text to summarize
        length: "short", "medium", or "detailed"
        style: "paragraph" or "bullets"
        language: Target language for the summary
        
    Returns:
        dict with summary, token counts, and chunk info
        
    Raises:
        ValueError: If text is empty or API key is missing
        Exception: If Gemini API call fails
    """
    if not text or not text.strip():
        raise ValueError("Text is empty. Nothing to summarize.")
    
    # Count tokens in original text
    original_tokens = count_tokens(text)
    logger.info(f"Summarizing {original_tokens} tokens (length={length})")
    
    # --- FREE MODE FALLBACK ---
    if not init_gemini():
        logger.info("No Gemini API key found. Using Free Mode Fallback.")
        words = text.split()
        summary_text = "[FREE MODE ACTIVE - Gemini Key Not Set]\n\n"
        
        if length == "short":
            summary_text += " ".join(words[:40]) + ("..." if len(words) > 40 else "")
        elif length == "medium":
            summary_text += " ".join(words[:120]) + ("..." if len(words) > 120 else "")
        else:
            summary_text += " ".join(words[:300]) + ("..." if len(words) > 300 else "")
            
        summary_text += "\n\n(This is a basic text extraction. To get real AI summaries, please add your GEMINI_API_KEY in the .env file)."
        
        return {
            "summary": summary_text,
            "original_tokens": original_tokens,
            "summary_tokens": len(summary_text.split()),
            "chunks_processed": 1,
            "compression_ratio": 1.0,
        }
    # --------------------------
    
    # Get the appropriate prompt
    length_prompts = SUMMARY_PROMPTS.get(length, SUMMARY_PROMPTS["medium"])
    system_prompt = length_prompts.get(style, length_prompts["paragraph"])
    
    # Add language instruction if not English
    if language.lower() != "english":
        system_prompt += f"\n\nWrite the summary in {language}."
    
    # Split into chunks if needed
    chunks = chunk_text(text, max_tokens=3000)
    
    if len(chunks) == 1:
        # Simple case: text fits in one chunk
        summary = await _call_gemini(system_prompt, chunks[0])
    else:
        # Map-Reduce: summarize each chunk, then combine
        logger.info(f"Using map-reduce with {len(chunks)} chunks")
        
        # MAP: Summarize each chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Summarizing chunk {i + 1}/{len(chunks)}")
            chunk_summary = await _call_gemini(
                "Summarize this section concisely, preserving key information:",
                chunk
            )
            chunk_summaries.append(chunk_summary)
        
        # REDUCE: Combine all chunk summaries into one final summary
        combined = "\n\n".join(chunk_summaries)
        logger.info(f"Reducing {len(chunk_summaries)} chunk summaries into final summary")
        
        summary = await _call_gemini(
            (
                f"{system_prompt}\n\n"
                "The following are summaries of different sections of a longer text. "
                "Combine them into one cohesive summary:"
            ),
            combined
        )
    
    summary_tokens = count_tokens(summary)
    
    return {
        "summary": summary,
        "original_tokens": original_tokens,
        "summary_tokens": summary_tokens,
        "chunks_processed": len(chunks),
        "compression_ratio": round(original_tokens / max(summary_tokens, 1), 1),
    }


async def _call_gemini(system_prompt: str, text: str) -> str:
    """
    Make a single call to Gemini 1.5 Flash.
    """
    try:
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=system_prompt
        )
        
        response = await model.generate_content_async(
            text,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=1000,
            )
        )
        
        if not response.text:
            raise ValueError("Gemini returned empty response")
        
        return response.text.strip()
        
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise ValueError(f"Gemini API failed: {str(e)}")
