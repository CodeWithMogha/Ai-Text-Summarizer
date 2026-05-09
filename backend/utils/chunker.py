"""
AI Summarization Platform — Token-Aware Text Chunker

WHY THIS EXISTS:
GPT-3.5-turbo has a 16K token context window. If someone uploads a 200-page PDF,
that's ~100,000 tokens — way too much for a single API call.

Solution: Split the text into chunks that fit within the token limit,
summarize each chunk, then summarize the summaries. This is called "map-reduce."

Think of it like reading a textbook:
- You read chapter by chapter (map — summarize each chapter)
- Then you write an overall summary from your chapter notes (reduce)
"""

import tiktoken
from utils.logger import logger


def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """
    Count the exact number of tokens in a text string.
    
    WHY NOT JUST USE len(text.split())?
    Because GPT doesn't tokenize by spaces. "don't" is 2 tokens (don, 't).
    "Hello" is 1 token, but "antidisestablishmentarianism" is 6 tokens.
    tiktoken gives you the EXACT count GPT will use.
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        # Fallback: rough estimate (1 token ≈ 4 characters)
        return len(text) // 4


def chunk_text(
    text: str,
    max_tokens: int = 3000,
    overlap_tokens: int = 200,
    model: str = "gpt-3.5-turbo"
) -> list[str]:
    """
    Split text into overlapping chunks that fit within the token limit.
    
    Args:
        text: The full text to split
        max_tokens: Maximum tokens per chunk (leave room for the prompt)
        overlap_tokens: Tokens of overlap between chunks to preserve context
        model: The model name for accurate token counting
        
    Returns:
        List of text chunks
        
    WHY OVERLAP?
    Imagine splitting a sentence right in the middle of an important idea:
    Chunk 1: "The company's revenue grew by 500% because"
    Chunk 2: "they launched a new product line in Asia."
    
    Without overlap, each chunk's summary misses the full picture.
    With overlap, chunk 2 starts with "...revenue grew by 500% because they launched..."
    so the summarizer gets the complete thought.
    """
    total_tokens = count_tokens(text, model)
    
    # If the text fits in a single chunk, return it as-is
    if total_tokens <= max_tokens:
        logger.info(f"Text fits in single chunk ({total_tokens} tokens)")
        return [text]
    
    logger.info(
        f"Splitting {total_tokens} tokens into chunks "
        f"(max {max_tokens} per chunk, {overlap_tokens} overlap)"
    )
    
    # Use tiktoken for precise splitting
    try:
        encoding = tiktoken.encoding_for_model(model)
    except Exception:
        encoding = tiktoken.get_encoding("cl100k_base")
    
    tokens = encoding.encode(text)
    chunks = []
    start = 0
    
    while start < len(tokens):
        # Take a chunk of max_tokens
        end = start + max_tokens
        
        # Don't go past the end
        if end > len(tokens):
            end = len(tokens)
        
        # Decode this chunk back to text
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)
        
        # Move forward by (max_tokens - overlap)
        # This creates the overlap with the next chunk
        start += max_tokens - overlap_tokens
    
    logger.info(f"Created {len(chunks)} chunks")
    return chunks
