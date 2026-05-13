"""PDF summarization router."""

import os
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from services.pdf_extractor import extract_text_from_pdf
from services.summarizer import summarize_text
from services.audio_extractor import cleanup_temp_files
from utils.logger import logger

router = APIRouter(prefix="/summarize", tags=["PDF Summarization"])

TEMP_DIR = os.getenv("TEMP_DIR", "./temp")
MAX_PDF_SIZE = int(os.getenv("MAX_PDF_SIZE", 10 * 1024 * 1024))


@router.post("/pdf")
async def summarize_pdf_endpoint(
    file: UploadFile = File(..., description="PDF file to summarize"),
    length: str = Form(default="medium"),
    style: str = Form(default="paragraph"),
    language: str = Form(default="english"),
):
    """Summarize a PDF file."""
    temp_path = None

    try:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail={"error": "invalid_file_type", "message": "Please upload a PDF file."})

        if file.content_type and file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail={"error": "invalid_content_type", "message": f"Expected application/pdf, got {file.content_type}"})

        if length not in ("short", "medium", "detailed"):
            length = "medium"

        content = await file.read()

        if len(content) > MAX_PDF_SIZE:
            size_mb = len(content) / 1024 / 1024
            max_mb = MAX_PDF_SIZE / 1024 / 1024
            raise HTTPException(status_code=413, detail={"error": "file_too_large", "message": f"PDF is {size_mb:.1f}MB. Max is {max_mb:.0f}MB."})

        if len(content) == 0:
            raise HTTPException(status_code=400, detail={"error": "empty_file", "message": "The uploaded file is empty."})

        os.makedirs(TEMP_DIR, exist_ok=True)
        file_id = str(uuid.uuid4())[:8]
        temp_path = os.path.join(TEMP_DIR, f"{file_id}_{file.filename}")

        with open(temp_path, "wb") as f:
            f.write(content)

        logger.info(f"PDF saved: {temp_path} ({len(content) / 1024:.1f}KB)")

        extraction = extract_text_from_pdf(temp_path)
        logger.info(f"Extracted {extraction['total_characters']} chars from {extraction['pages_with_text']}/{extraction['total_pages']} pages")

        result = await summarize_text(text=extraction["text"], length=length, style=style, language=language)

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
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "pdf_error", "message": str(e)})
    except Exception as e:
        logger.error(f"PDF summarization failed: {e}")
        raise HTTPException(status_code=500, detail={"error": "internal_error", "message": "Failed to process PDF."})
    finally:
        if temp_path:
            cleanup_temp_files(temp_path)
