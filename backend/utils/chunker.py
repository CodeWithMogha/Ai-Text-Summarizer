"""Token-aware text chunker for map-reduce summarization."""

import tiktoken
from utils.logger import logger


def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Count the exact number of tokens in a text string using tiktoken."""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
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
        max_tokens: Maximum tokens per chunk
        overlap_tokens: Tokens of overlap between chunks to preserve context
        model: The model name for accurate token counting

    Returns:
        List of text chunks
    """
    total_tokens = count_tokens(text, model)

    if total_tokens <= max_tokens:
        logger.info(f"Text fits in single chunk ({total_tokens} tokens)")
        return [text]

    logger.info(
        f"Splitting {total_tokens} tokens into chunks "
        f"(max {max_tokens} per chunk, {overlap_tokens} overlap)"
    )

    try:
        encoding = tiktoken.encoding_for_model(model)
    except Exception:
        encoding = tiktoken.get_encoding("cl100k_base")

    tokens = encoding.encode(text)
    chunks = []
    start = 0

    while start < len(tokens):
        end = start + max_tokens

        if end > len(tokens):
            end = len(tokens)

        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)

        start += max_tokens - overlap_tokens

    logger.info(f"Created {len(chunks)} chunks")
    return chunks
