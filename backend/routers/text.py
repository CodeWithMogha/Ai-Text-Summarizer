"""Text summarization router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from services.summarizer import summarize_text
from utils.cleaner import clean_text_input
from utils.logger import logger

router = APIRouter(prefix="/summarize", tags=["Text Summarization"])


class TextRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=100000, description="Text to summarize (10-100,000 chars)")
    length: str = Field(default="medium", pattern="^(short|medium|detailed)$")
    style: str = Field(default="paragraph", pattern="^(paragraph|bullets)$")
    language: str = Field(default="english")


class TextResponse(BaseModel):
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
    """Summarize raw text."""
    try:
        cleaned_text = clean_text_input(request.text)

        if not cleaned_text:
            raise HTTPException(
                status_code=400,
                detail={"error": "empty_text", "message": "Text is empty after cleaning."}
            )

        logger.info(f"Text summarization: {len(cleaned_text)} chars, length={request.length}")

        result = await summarize_text(
            text=cleaned_text, length=request.length, style=request.style, language=request.language
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
        raise HTTPException(status_code=400, detail={"error": "validation_error", "message": str(e)})
    except Exception as e:
        logger.error(f"Text summarization failed: {e}")
        raise HTTPException(status_code=500, detail={"error": "internal_error", "message": "An unexpected error occurred."})
