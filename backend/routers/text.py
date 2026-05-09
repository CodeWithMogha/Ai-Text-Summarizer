"""
AI Summarization Platform — Text Summarization Router

THE SIMPLEST PIPELINE:
User sends text → we validate → chunk → GPT → return summary.
No file handling, no extraction. Just pure text in, summary out.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from services.summarizer import summarize_text
from utils.cleaner import clean_text_input
from utils.logger import logger


router = APIRouter(prefix="/summarize", tags=["Text Summarization"])


class TextRequest(BaseModel):
    """
    Request body for text summarization.
    
    WHY Pydantic models?
    FastAPI uses Pydantic for automatic validation. If someone sends
    {text: 123} instead of {text: "hello"}, FastAPI returns a 422 error
    automatically — you don't need to write validation code.
    """
    text: str = Field(
        ...,  # Required field
        min_length=10,
        max_length=100000,
        description="The text to summarize (10-100,000 characters)"
    )
    length: str = Field(
        default="medium",
        pattern="^(short|medium|detailed)$",
        description="Summary length: short, medium, or detailed"
    )
    style: str = Field(
        default="paragraph",
        pattern="^(paragraph|bullets)$",
        description="Summary style: paragraph or bullets"
    )
    language: str = Field(
        default="english",
        description="Target language for the summary"
    )


class TextResponse(BaseModel):
    """Structured response for text summarization."""
    success: bool
    summary: str
    original_length: int
    summary_length: int
    original_tokens: int
    summary_tokens: int
    compression_ratio: float
    chunks_processed: int


@router.post("/text", response_model=TextResponse)
async def summarize_text_endpoint(request: TextRequest):
    """
    Summarize raw text using GPT-3.5-turbo.
    
    - Accepts text between 10 and 100,000 characters
    - Supports short/medium/detailed summary lengths
    - Automatically chunks long text using map-reduce
    """
    try:
        # Clean the input text (collapse whitespace, etc.)
        cleaned_text = clean_text_input(request.text)
        
        if not cleaned_text:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "empty_text",
                    "message": "Text is empty after cleaning. Please provide meaningful text."
                }
            )
        
        logger.info(
            f"Text summarization request: {len(cleaned_text)} chars, "
            f"length={request.length}"
        )
        
        # Call the summarizer service
        result = await summarize_text(
            text=cleaned_text,
            length=request.length,
            style=request.style,
            language=request.language,
        )
        
        return TextResponse(
            success=True,
            summary=result["summary"],
            original_length=len(cleaned_text),
            summary_length=len(result["summary"]),
            original_tokens=result["original_tokens"],
            summary_tokens=result["summary_tokens"],
            compression_ratio=result["compression_ratio"],
            chunks_processed=result["chunks_processed"],
        )
        
    except ValueError as e:
        # ValueError = known, user-facing error
        raise HTTPException(
            status_code=400,
            detail={"error": "validation_error", "message": str(e)}
        )
    except Exception as e:
        # Unexpected error — log it, return generic message
        logger.error(f"Text summarization failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "An unexpected error occurred. Please try again."
            }
        )
