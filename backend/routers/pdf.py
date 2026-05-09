"""
AI Summarization Platform — PDF Summarization Router

THE PDF PIPELINE:
User uploads PDF → save to temp → pdfplumber extracts text →
chunk → GPT summarizes → clean up temp file → return summary.

CRITICAL: Always clean up temp files in a finally block.
If the summarization fails and you don't clean up, temp files accumulate
until your server runs out of disk space. This WILL happen in production.
"""

import os
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from services.pdf_extractor import extract_text_from_pdf
from services.summarizer import summarize_text
from services.audio_extractor import cleanup_temp_files
from utils.logger import logger


router = APIRouter(prefix="/summarize", tags=["PDF Summarization"])

# Config
TEMP_DIR = os.getenv("TEMP_DIR", "./temp")
MAX_PDF_SIZE = int(os.getenv("MAX_PDF_SIZE", 10 * 1024 * 1024))  # 10MB default


@router.post("/pdf")
async def summarize_pdf_endpoint(
    file: UploadFile = File(..., description="PDF file to summarize"),
    length: str = Form(default="medium", description="short|medium|detailed"),
    style: str = Form(default="paragraph", description="paragraph|bullets"),
    language: str = Form(default="english", description="Target language"),
):
    """
    Summarize a PDF file.
    
    - Accepts PDF files up to 10MB
    - Extracts text using pdfplumber
    - Handles scanned PDFs (returns error with suggestion)
    - Handles password-protected PDFs (returns clear error)
    """
    temp_path = None
    
    try:
        # ── VALIDATION ──────────────────────────────────────────────
        
        # Check file type
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_file_type",
                    "message": "Please upload a PDF file (.pdf extension required)."
                }
            )
        
        # Check content type
        if file.content_type and file.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_content_type",
                    "message": f"Expected application/pdf, got {file.content_type}"
                }
            )
        
        # Validate length parameter
        if length not in ("short", "medium", "detailed"):
            length = "medium"
        
        # Read file content
        content = await file.read()
        
        # Check file size
        if len(content) > MAX_PDF_SIZE:
            size_mb = len(content) / 1024 / 1024
            max_mb = MAX_PDF_SIZE / 1024 / 1024
            raise HTTPException(
                status_code=413,
                detail={
                    "error": "file_too_large",
                    "message": (
                        f"PDF is {size_mb:.1f}MB. Maximum allowed is {max_mb:.0f}MB. "
                        "Try splitting the PDF into smaller files."
                    )
                }
            )
        
        if len(content) == 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "empty_file",
                    "message": "The uploaded file is empty."
                }
            )
        
        # ── SAVE TO TEMP ────────────────────────────────────────────
        
        os.makedirs(TEMP_DIR, exist_ok=True)
        file_id = str(uuid.uuid4())[:8]
        temp_path = os.path.join(TEMP_DIR, f"{file_id}_{file.filename}")
        
        with open(temp_path, "wb") as f:
            f.write(content)
        
        logger.info(
            f"PDF saved to temp: {temp_path} ({len(content) / 1024:.1f}KB)"
        )
        
        # ── EXTRACT TEXT ────────────────────────────────────────────
        
        extraction = extract_text_from_pdf(temp_path)
        
        logger.info(
            f"PDF text extracted: {extraction['total_characters']} chars "
            f"from {extraction['pages_with_text']}/{extraction['total_pages']} pages"
        )
        
        # ── SUMMARIZE ───────────────────────────────────────────────
        
        result = await summarize_text(
            text=extraction["text"],
            length=length,
            style=style,
            language=language,
        )
        
        return {
            "success": True,
            "summary": result["summary"],
            "original_length": extraction["total_characters"],
            "summary_length": len(result["summary"]),
            "pages_processed": extraction["total_pages"],
            "pages_with_text": extraction["pages_with_text"],
            "original_tokens": result["original_tokens"],
            "summary_tokens": result["summary_tokens"],
            "compression_ratio": result["compression_ratio"],
            "chunks_processed": result["chunks_processed"],
        }
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "pdf_error", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"PDF summarization failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "Failed to process PDF. Please try again."
            }
        )
    finally:
        # ALWAYS clean up temp files — even if an error occurred
        if temp_path:
            cleanup_temp_files(temp_path)
