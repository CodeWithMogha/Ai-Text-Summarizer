"""Transcript and text cleaner for pre-processing before summarization."""

import re
from utils.logger import logger


FILLER_WORDS = [
    r"\bum\b", r"\buh\b", r"\blike\b", r"\byou know\b",
    r"\bso\b(?=,)", r"\bactually\b", r"\bbasically\b",
    r"\bliterally\b", r"\bhonestly\b", r"\bi mean\b",
    r"\bkind of\b", r"\bsort of\b", r"\bright\b(?=[\?,])",
]


def clean_transcript(text: str) -> str:
    """
    Clean a raw Whisper transcript for better summarization.

    Removes filler words, repeated words, and fixes spacing/punctuation.
    """
    if not text or not text.strip():
        return ""

    logger.info(f"Cleaning transcript ({len(text)} chars)")
    original_length = len(text)

    for filler in FILLER_WORDS:
        text = re.sub(filler, "", text, flags=re.IGNORECASE)

    text = re.sub(r"\b(\w+)\s+\1\b", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([.,!?;:])", r"\1", text)
    text = re.sub(r"([.,!?;:])(\w)", r"\1 \2", text)
    text = re.sub(r"\.{2,}", ".", text)

    def capitalize_after_period(match):
        return match.group(1) + match.group(2).upper()

    text = re.sub(r"([.!?]\s+)([a-z])", capitalize_after_period, text)

    text = text.strip()
    if text:
        text = text[0].upper() + text[1:]

    cleaned_length = len(text)
    removed = original_length - cleaned_length
    logger.info(
        f"Transcript cleaned: {original_length} → {cleaned_length} chars "
        f"(removed {removed} chars, {removed * 100 // max(original_length, 1)}%)"
    )

    return text


def clean_text_input(text: str) -> str:
    """Light cleaning for user-provided text (collapse whitespace, trim)."""
    if not text or not text.strip():
        return ""

    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[^\S\n]+", " ", text)

    return text.strip()
