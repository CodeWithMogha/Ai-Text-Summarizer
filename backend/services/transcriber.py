"""
AI Summarization Platform — Whisper Transcription Service

WHY LOCAL WHISPER vs OPENAI WHISPER API?
- Local: Free, unlimited, no internet needed. But needs RAM and is slower.
- API: $0.006/min, fast, no RAM needed. But costs money.
For a student project, local Whisper is perfect. In production, you'd 
probably use the API for speed and switch to local for cost at scale.

CRITICAL PATTERN — MODEL PRE-LOADING:
We load the Whisper model ONCE at startup, not on every request.
Loading takes 10-30 seconds. If you loaded it per request, every
user would wait 30 extra seconds. That's the difference between
"this is slow" and "this is broken."
"""

import os
import whisper
import asyncio
from functools import partial
from typing import Optional
from utils.logger import logger


# Global model reference — loaded once, used forever
_whisper_model = None


def load_whisper_model(model_name: Optional[str] = None) -> None:
    """
    Pre-load the Whisper model into memory.
    Call this at FastAPI startup, not during request handling.
    
    Model sizes and their trade-offs:
    ┌──────────┬──────────┬───────────┬──────────────┐
    │ Model    │ RAM      │ Speed     │ Accuracy     │
    ├──────────┼──────────┼───────────┼──────────────┤
    │ tiny     │ ~1 GB    │ ~32x      │ Decent       │
    │ base     │ ~1 GB    │ ~16x      │ Good         │
    │ small    │ ~2 GB    │ ~6x       │ Great        │
    │ medium   │ ~5 GB    │ ~2x       │ Very good    │
    │ large    │ ~10 GB   │ 1x        │ Best         │
    └──────────┴──────────┴───────────┴──────────────┘
    
    For development: use "base" (good accuracy, fast)
    For Render free tier: use "tiny" (fits in 512MB RAM)
    For production: use "small" or the OpenAI API instead
    """
    global _whisper_model
    
    if model_name is None:
        model_name = os.getenv("WHISPER_MODEL", "base")
    
    logger.info(f"Loading Whisper model: {model_name} (this may take 10-30s)...")
    
    try:
        _whisper_model = whisper.load_model(model_name)
        logger.info(f"Whisper model '{model_name}' loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load Whisper model: {e}")
        raise RuntimeError(
            f"Failed to load Whisper model '{model_name}'. "
            f"Make sure you have enough RAM. Error: {e}"
        )


def get_whisper_model():
    """Get the pre-loaded Whisper model."""
    if _whisper_model is None:
        raise RuntimeError(
            "Whisper model not loaded. This means load_whisper_model() "
            "was not called at startup. Check main.py startup events."
        )
    return _whisper_model


async def transcribe_audio(audio_path: str) -> dict:
    """
    Transcribe an audio file using the pre-loaded Whisper model.
    
    WHY async + run_in_executor?
    Whisper transcription is CPU-intensive (it's running a neural network).
    If we ran it directly in an async function, it would BLOCK the entire
    FastAPI server — no other requests could be processed.
    
    run_in_executor() runs the CPU work in a thread pool, keeping the
    async event loop free to handle other requests.
    
    Args:
        audio_path: Path to the audio file (ideally 16kHz mono WAV)
        
    Returns:
        dict with transcript text, detected language, and duration
        
    Raises:
        ValueError: If transcription fails or produces empty output
    """
    if not os.path.exists(audio_path):
        raise ValueError(f"Audio file not found: {audio_path}")
    
    file_size = os.path.getsize(audio_path)
    logger.info(
        f"Starting transcription: {audio_path} "
        f"({file_size / 1024 / 1024:.1f} MB)"
    )
    
    model = get_whisper_model()
    
    # Run CPU-intensive transcription in thread pool
    loop = asyncio.get_event_loop()
    
    try:
        result = await loop.run_in_executor(
            None,  # Use default thread pool
            partial(
                model.transcribe,
                audio_path,
                fp16=False,  # Use FP32 on CPU (FP16 is for GPU only)
                language=None,  # Auto-detect language
                task="transcribe",  # "transcribe" keeps original language
            )
        )
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        raise ValueError(
            f"Transcription failed. The audio may be corrupted or "
            f"in an unsupported format. Error: {str(e)}"
        )
    
    transcript = result.get("text", "").strip()
    detected_language = result.get("language", "unknown")
    
    # Validate the output
    if not transcript:
        raise ValueError(
            "Whisper produced an empty transcript. This usually means:\n"
            "1. The audio has no speech (music only, silence)\n"
            "2. The audio quality is too poor\n"
            "3. The language is not supported"
        )
    
    # Check for garbage output (Whisper sometimes hallucinates on silence)
    if len(transcript) < 10 and len(set(transcript.split())) < 3:
        raise ValueError(
            "Whisper produced very little usable text. "
            "The audio may not contain clear speech."
        )
    
    # Extract segments for timestamps if available
    segments = []
    for seg in result.get("segments", []):
        segments.append({
            "start": round(seg["start"], 2),
            "end": round(seg["end"], 2),
            "text": seg["text"].strip(),
        })
    
    logger.info(
        f"Transcription complete: {len(transcript)} chars, "
        f"language={detected_language}, segments={len(segments)}"
    )
    
    return {
        "transcript": transcript,
        "language": detected_language,
        "segments": segments,
        "character_count": len(transcript),
    }
