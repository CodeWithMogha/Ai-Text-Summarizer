"""Whisper transcription service with model pre-loading."""

import os
import whisper
import asyncio
from functools import partial
from typing import Optional
from utils.logger import logger

_whisper_model = None


def load_whisper_model(model_name: Optional[str] = None) -> None:
    """Pre-load the Whisper model into memory at startup."""
    global _whisper_model
    if model_name is None:
        model_name = os.getenv("WHISPER_MODEL", "base")

    logger.info(f"Loading Whisper model: {model_name}...")
    try:
        _whisper_model = whisper.load_model(model_name)
        logger.info(f"Whisper model '{model_name}' loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load Whisper model: {e}")
        raise RuntimeError(f"Failed to load Whisper model '{model_name}': {e}")


def get_whisper_model():
    """Get the pre-loaded Whisper model."""
    if _whisper_model is None:
        raise RuntimeError("Whisper model not loaded. Check main.py startup events.")
    return _whisper_model


async def transcribe_audio(audio_path: str) -> dict:
    """Transcribe an audio file using the pre-loaded Whisper model."""
    if not os.path.exists(audio_path):
        raise ValueError(f"Audio file not found: {audio_path}")

    file_size = os.path.getsize(audio_path)
    logger.info(f"Starting transcription: {audio_path} ({file_size / 1024 / 1024:.1f} MB)")

    model = get_whisper_model()
    loop = asyncio.get_event_loop()

    try:
        result = await loop.run_in_executor(
            None,
            partial(model.transcribe, audio_path, fp16=False, language=None, task="transcribe")
        )
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        raise ValueError(f"Transcription failed: {str(e)}")

    transcript = result.get("text", "").strip()
    detected_language = result.get("language", "unknown")

    if not transcript:
        raise ValueError("Whisper produced an empty transcript. The audio may have no speech.")

    if len(transcript) < 10 and len(set(transcript.split())) < 3:
        raise ValueError("Whisper produced very little usable text.")

    segments = []
    for seg in result.get("segments", []):
        segments.append({
            "start": round(seg["start"], 2),
            "end": round(seg["end"], 2),
            "text": seg["text"].strip(),
        })

    logger.info(f"Transcription complete: {len(transcript)} chars, lang={detected_language}")

    return {
        "transcript": transcript,
        "language": detected_language,
        "segments": segments,
        "character_count": len(transcript),
    }
