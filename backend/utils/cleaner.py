"""
AI Summarization Platform — Transcript Cleaner

WHY THIS EXISTS:
Raw Whisper transcripts look like this:
"Um, so like, you know, the the the company decided to, uh, launch a new product..."

After cleaning:
"The company decided to launch a new product..."

Clean text = better summaries from GPT. Garbage in, garbage out.
"""

import re
from utils.logger import logger


# Filler words to remove — these add no information
FILLER_WORDS = [
    r"\bum\b", r"\buh\b", r"\blike\b", r"\byou know\b",
    r"\bso\b(?=,)", r"\bactually\b", r"\bbasically\b",
    r"\bliterally\b", r"\bhonestly\b", r"\bi mean\b",
    r"\bkind of\b", r"\bsort of\b", r"\bright\b(?=[\?,])",
]


def clean_transcript(text: str) -> str:
    """
    Clean a raw Whisper transcript for better summarization.
    
    Steps:
    1. Remove filler words (um, uh, like, you know)
    2. Fix repeated words ("the the" → "the")
    3. Fix spacing and punctuation
    4. Collapse multiple spaces
    5. Fix capitalization after periods
    
    Args:
        text: Raw transcript from Whisper
        
    Returns:
        Cleaned transcript ready for summarization
    """
    if not text or not text.strip():
        return ""
    
    logger.info(f"Cleaning transcript ({len(text)} chars)")
    original_length = len(text)
    
    # Step 1: Remove filler words (case-insensitive)
    for filler in FILLER_WORDS:
        text = re.sub(filler, "", text, flags=re.IGNORECASE)
    
    # Step 2: Remove repeated words ("the the" → "the")
    text = re.sub(r"\b(\w+)\s+\1\b", r"\1", text, flags=re.IGNORECASE)
    
    # Step 3: Fix multiple spaces → single space
    text = re.sub(r"\s+", " ", text)
    
    # Step 4: Fix spacing around punctuation
    text = re.sub(r"\s+([.,!?;:])", r"\1", text)  # Remove space before punctuation
    text = re.sub(r"([.,!?;:])(\w)", r"\1 \2", text)  # Add space after punctuation
    
    # Step 5: Fix multiple periods
    text = re.sub(r"\.{2,}", ".", text)
    
    # Step 6: Capitalize after periods
    def capitalize_after_period(match):
        return match.group(1) + match.group(2).upper()
    
    text = re.sub(r"([.!?]\s+)([a-z])", capitalize_after_period, text)
    
    # Step 7: Ensure first character is capitalized
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
    """
    Light cleaning for user-provided text (not transcripts).
    We don't remove filler words since the user typed them intentionally.
    
    Steps:
    1. Strip leading/trailing whitespace
    2. Collapse multiple newlines to max 2
    3. Collapse multiple spaces to single space
    """
    if not text or not text.strip():
        return ""
    
    # Collapse excessive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    # Collapse multiple spaces (but not newlines)
    text = re.sub(r"[^\S\n]+", " ", text)
    
    return text.strip()
