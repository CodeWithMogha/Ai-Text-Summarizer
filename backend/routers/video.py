"""
AI Summarization Platform — Video Summarization Router

THE MOST COMPLEX PIPELINE:
Two entry points, same destination:

1. URL path:  URL → yt-dlp download → FFmpeg convert → Whisper → GPT → summary
2. Upload path: File → FFmpeg convert → Whisper → GPT → summary

This is where everything comes together. Audio extraction, transcription,
cleaning, chunking, and summarization all happen in sequence.

CRITICAL: Multiple temp files are created. ALL must be cleaned up in finally.
"""

import os
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from services.audio_extractor import (
    extract_audio_from_url,
    extract_audio_from_file,
    cleanup_temp_files,
)
from services.transcriber import transcribe_audio
from services.summarizer import summarize_text
from utils.cleaner import clean_transcript
from utils.logger import logger


router = APIRouter(prefix="/summarize", tags=["Video Summarization"])

# Config
TEMP_DIR = os.getenv("TEMP_DIR", "./temp")
MAX_VIDEO_SIZE = int(os.getenv("MAX_VIDEO_SIZE", 100 * 1024 * 1024))  # 100MB

# Supported video formats for upload
ALLOWED_VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv",
    ".mp3", ".wav", ".m4a", ".ogg", ".flac"  # Audio files too
}


class VideoURLRequest(BaseModel):
    """Request body for video URL summarization."""
    url: str = Field(
        ...,
        min_length=10,
        description="YouTube or other supported video URL"
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
    include_transcript: bool = Field(
        default=False,
        description="Whether to include the full transcript in response"
    )


@router.post("/video/url")
async def summarize_video_url(request: VideoURLRequest):
    """
    Summarize a video from a URL (YouTube, Vimeo, etc.).
    
    Pipeline: URL → yt-dlp → FFmpeg → Whisper → clean → GPT → summary
    
    - Supports YouTube, Vimeo, and 1000+ other sites
    - Auto-detects language
    - Handles private/unavailable videos with clear errors
    - 5-minute download timeout
    """
    audio_path = None
    
    try:
        # ── VALIDATION ──────────────────────────────────────────────
        
        url = request.url.strip()
        
        if not url.startswith(("http://", "https://")):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_url",
                    "message": "URL must start with http:// or https://"
                }
            )
        
        logger.info(f"Video URL summarization request: {url}")
        
        # ── STEP 1: DOWNLOAD AUDIO ──────────────────────────────────
        
        audio_result = await extract_audio_from_url(url)
        audio_path = audio_result["audio_path"]
        
        # ── STEP 2: TRANSCRIBE ───────────────────────────────────────
        
        transcription = await transcribe_audio(audio_path)
        raw_transcript = transcription["transcript"]
        detected_language = transcription["language"]
        
        # ── STEP 3: CLEAN TRANSCRIPT ────────────────────────────────
        
        cleaned_transcript = clean_transcript(raw_transcript)
        
        if not cleaned_transcript or len(cleaned_transcript) < 20:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "insufficient_transcript",
                    "message": (
                        "Could not extract enough speech from this video. "
                        "The video may have no speech, only music, or "
                        "the audio quality may be too poor."
                    )
                }
            )
        
        # ── STEP 4: SUMMARIZE ────────────────────────────────────────
        
        result = await summarize_text(
            text=cleaned_transcript,
            length=request.length,
            style=request.style,
            language=request.language,
        )
        
        # ── BUILD RESPONSE ───────────────────────────────────────────
        
        response = {
            "success": True,
            "summary": result["summary"],
            "detected_language": detected_language,
            "transcript_length": len(cleaned_transcript),
            "summary_length": len(result["summary"]),
            "original_tokens": result["original_tokens"],
            "summary_tokens": result["summary_tokens"],
            "compression_ratio": result["compression_ratio"],
            "chunks_processed": result["chunks_processed"],
            "source_url": url,
        }
        
        # Optionally include full transcript
        if request.include_transcript:
            response["transcript"] = cleaned_transcript
            response["segments"] = transcription.get("segments", [])
        
        return response
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "video_error", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Video URL summarization failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "Failed to process video. Please try again."
            }
        )
    finally:
        # Clean up ALL temp files
        if audio_path:
            cleanup_temp_files(audio_path)


@router.post("/video/upload")
async def summarize_video_upload(
    file: UploadFile = File(..., description="Video or audio file"),
    length: str = Form(default="medium", description="short|medium|detailed"),
    style: str = Form(default="paragraph", description="paragraph|bullets"),
    language: str = Form(default="english", description="Target language"),
    include_transcript: bool = Form(default=False, description="Include transcript"),
):
    """
    Summarize an uploaded video or audio file.
    
    Pipeline: File → FFmpeg → Whisper → clean → GPT → summary
    
    - Supports MP4, MKV, AVI, MOV, WebM, MP3, WAV, M4A, etc.
    - Maximum file size: 100MB
    - Auto-detects language
    """
    temp_video_path = None
    audio_path = None
    
    try:
        # ── VALIDATION ──────────────────────────────────────────────
        
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "no_filename",
                    "message": "File must have a filename."
                }
            )
        
        # Check file extension
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_VIDEO_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_file_type",
                    "message": (
                        f"Unsupported file type: {ext}. "
                        f"Supported: {', '.join(sorted(ALLOWED_VIDEO_EXTENSIONS))}"
                    )
                }
            )
        
        # Validate length parameter
        if length not in ("short", "medium", "detailed"):
            length = "medium"
        
        # Read and check file size
        content = await file.read()
        
        if len(content) == 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "empty_file",
                    "message": "The uploaded file is empty."
                }
            )
        
        if len(content) > MAX_VIDEO_SIZE:
            size_mb = len(content) / 1024 / 1024
            max_mb = MAX_VIDEO_SIZE / 1024 / 1024
            raise HTTPException(
                status_code=413,
                detail={
                    "error": "file_too_large",
                    "message": (
                        f"File is {size_mb:.1f}MB. Maximum allowed is {max_mb:.0f}MB. "
                        "Try compressing the video or using a URL instead."
                    )
                }
            )
        
        # ── SAVE TO TEMP ────────────────────────────────────────────
        
        os.makedirs(TEMP_DIR, exist_ok=True)
        file_id = str(uuid.uuid4())[:8]
        temp_video_path = os.path.join(TEMP_DIR, f"{file_id}_{file.filename}")
        
        with open(temp_video_path, "wb") as f:
            f.write(content)
        
        logger.info(
            f"Video saved to temp: {temp_video_path} "
            f"({len(content) / 1024 / 1024:.1f}MB)"
        )
        
        # ── STEP 1: EXTRACT AUDIO ───────────────────────────────────
        
        audio_result = await extract_audio_from_file(temp_video_path)
        audio_path = audio_result["audio_path"]
        
        # ── STEP 2: TRANSCRIBE ───────────────────────────────────────
        
        transcription = await transcribe_audio(audio_path)
        raw_transcript = transcription["transcript"]
        detected_language = transcription["language"]
        
        # ── STEP 3: CLEAN TRANSCRIPT ────────────────────────────────
        
        cleaned_transcript = clean_transcript(raw_transcript)
        
        if not cleaned_transcript or len(cleaned_transcript) < 20:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "insufficient_transcript",
                    "message": (
                        "Could not extract enough speech from this file. "
                        "The file may not contain speech or the audio "
                        "quality may be too poor."
                    )
                }
            )
        
        # ── STEP 4: SUMMARIZE ────────────────────────────────────────
        
        result = await summarize_text(
            text=cleaned_transcript,
            length=length,
            style=style,
            language=language,
        )
        
        # ── BUILD RESPONSE ───────────────────────────────────────────
        
        response = {
            "success": True,
            "summary": result["summary"],
            "detected_language": detected_language,
            "transcript_length": len(cleaned_transcript),
            "summary_length": len(result["summary"]),
            "original_tokens": result["original_tokens"],
            "summary_tokens": result["summary_tokens"],
            "compression_ratio": result["compression_ratio"],
            "chunks_processed": result["chunks_processed"],
            "filename": file.filename,
        }
        
        if include_transcript:
            response["transcript"] = cleaned_transcript
            response["segments"] = transcription.get("segments", [])
        
        return response
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "video_error", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Video upload summarization failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "Failed to process video file. Please try again."
            }
        )
    finally:
        # Clean up ALL temp files — this is non-negotiable
        cleanup_temp_files(
            temp_video_path or "",
            audio_path or "",
        )
