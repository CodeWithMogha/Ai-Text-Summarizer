"""Video summarization router (URL and upload)."""

import os
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from services.audio_extractor import extract_audio_from_url, extract_audio_from_file, cleanup_temp_files
from services.transcriber import transcribe_audio
from services.summarizer import summarize_text
from utils.cleaner import clean_transcript
from utils.logger import logger

router = APIRouter(prefix="/summarize", tags=["Video Summarization"])

TEMP_DIR = os.getenv("TEMP_DIR", "./temp")
MAX_VIDEO_SIZE = int(os.getenv("MAX_VIDEO_SIZE", 100 * 1024 * 1024))

ALLOWED_VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv",
    ".mp3", ".wav", ".m4a", ".ogg", ".flac"
}


class VideoURLRequest(BaseModel):
    url: str = Field(..., min_length=10)
    length: str = Field(default="medium", pattern="^(short|medium|detailed)$")
    style: str = Field(default="paragraph", pattern="^(paragraph|bullets)$")
    language: str = Field(default="english")
    include_transcript: bool = Field(default=False)


@router.post("/video/url")
async def summarize_video_url(request: VideoURLRequest):
    """Summarize a video from URL. Pipeline: URL → yt-dlp → FFmpeg → Whisper → GPT."""
    audio_path = None

    try:
        url = request.url.strip()
        if not url.startswith(("http://", "https://")):
            raise HTTPException(status_code=400, detail={"error": "invalid_url", "message": "URL must start with http:// or https://"})

        logger.info(f"Video URL summarization: {url}")

        audio_result = await extract_audio_from_url(url)
        audio_path = audio_result["audio_path"]

        transcription = await transcribe_audio(audio_path)
        raw_transcript = transcription["transcript"]
        detected_language = transcription["language"]

        cleaned_transcript = clean_transcript(raw_transcript)

        if not cleaned_transcript or len(cleaned_transcript) < 20:
            raise HTTPException(status_code=400, detail={"error": "insufficient_transcript", "message": "Could not extract enough speech from this video."})

        result = await summarize_text(text=cleaned_transcript, length=request.length, style=request.style, language=request.language)

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

        if request.include_transcript:
            response["transcript"] = cleaned_transcript
            response["segments"] = transcription.get("segments", [])

        return response

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "video_error", "message": str(e)})
    except Exception as e:
        logger.error(f"Video URL summarization failed: {e}")
        raise HTTPException(status_code=500, detail={"error": "internal_error", "message": "Failed to process video."})
    finally:
        if audio_path:
            cleanup_temp_files(audio_path)


@router.post("/video/upload")
async def summarize_video_upload(
    file: UploadFile = File(...),
    length: str = Form(default="medium"),
    style: str = Form(default="paragraph"),
    language: str = Form(default="english"),
    include_transcript: bool = Form(default=False),
):
    """Summarize an uploaded video/audio file. Pipeline: File → FFmpeg → Whisper → GPT."""
    temp_video_path = None
    audio_path = None

    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail={"error": "no_filename", "message": "File must have a filename."})

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_VIDEO_EXTENSIONS:
            raise HTTPException(status_code=400, detail={"error": "invalid_file_type", "message": f"Unsupported: {ext}. Supported: {', '.join(sorted(ALLOWED_VIDEO_EXTENSIONS))}"})

        if length not in ("short", "medium", "detailed"):
            length = "medium"

        content = await file.read()

        if len(content) == 0:
            raise HTTPException(status_code=400, detail={"error": "empty_file", "message": "The uploaded file is empty."})

        if len(content) > MAX_VIDEO_SIZE:
            size_mb = len(content) / 1024 / 1024
            max_mb = MAX_VIDEO_SIZE / 1024 / 1024
            raise HTTPException(status_code=413, detail={"error": "file_too_large", "message": f"File is {size_mb:.1f}MB. Max is {max_mb:.0f}MB."})

        os.makedirs(TEMP_DIR, exist_ok=True)
        file_id = str(uuid.uuid4())[:8]
        temp_video_path = os.path.join(TEMP_DIR, f"{file_id}_{file.filename}")

        with open(temp_video_path, "wb") as f:
            f.write(content)

        logger.info(f"Video saved: {temp_video_path} ({len(content) / 1024 / 1024:.1f}MB)")

        audio_result = await extract_audio_from_file(temp_video_path)
        audio_path = audio_result["audio_path"]

        transcription = await transcribe_audio(audio_path)
        raw_transcript = transcription["transcript"]
        detected_language = transcription["language"]

        cleaned_transcript = clean_transcript(raw_transcript)

        if not cleaned_transcript or len(cleaned_transcript) < 20:
            raise HTTPException(status_code=400, detail={"error": "insufficient_transcript", "message": "Could not extract enough speech from this file."})

        result = await summarize_text(text=cleaned_transcript, length=length, style=style, language=language)

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
        raise HTTPException(status_code=400, detail={"error": "video_error", "message": str(e)})
    except Exception as e:
        logger.error(f"Video upload summarization failed: {e}")
        raise HTTPException(status_code=500, detail={"error": "internal_error", "message": "Failed to process video file."})
    finally:
        cleanup_temp_files(temp_video_path or "", audio_path or "")
