"""
AI Summarization Platform — Audio Extractor

WHY TWO PATHS?
1. YouTube URL → yt-dlp downloads ONLY the audio (not the full video)
2. Uploaded file → FFmpeg extracts the audio track

Both paths end with a 16kHz mono WAV file — the format Whisper works best with.

ANALOGY: Think of yt-dlp as a vending machine — you put in a URL, it gives you audio.
FFmpeg is a Swiss Army knife — it can convert anything to anything.
"""

import os
import uuid
import subprocess
import asyncio
import shutil
from typing import Optional
from utils.logger import logger


TEMP_DIR = os.getenv("TEMP_DIR", "./temp")


def _ensure_temp_dir():
    """Create temp directory if it doesn't exist."""
    os.makedirs(TEMP_DIR, exist_ok=True)


async def extract_audio_from_url(url: str) -> dict:
    """
    Download audio from a YouTube (or supported) URL using yt-dlp.
    
    Args:
        url: YouTube or other supported video URL
        
    Returns:
        dict with audio_path, title, duration
        
    Raises:
        ValueError: If URL is invalid, private, or download fails
    """
    _ensure_temp_dir()
    
    # Generate unique filename to avoid collisions with concurrent requests
    file_id = str(uuid.uuid4())[:8]
    output_path = os.path.join(TEMP_DIR, f"{file_id}_audio.wav")
    
    logger.info(f"Downloading audio from URL: {url}")
    
    # yt-dlp command breakdown:
    # -x                  → extract audio only (don't download video)
    # --audio-format wav  → convert to WAV
    # --audio-quality 0   → best quality
    # --no-playlist       → don't download entire playlist if URL is from one
    # -o output_path      → where to save
    # --max-filesize 100m → safety limit
    # --socket-timeout 30 → don't hang forever on slow connections
    # Try to find yt-dlp in PATH, then fallback to venv
    yt_dlp_executable = shutil.which("yt-dlp")
    if not yt_dlp_executable:
        venv_path = os.path.join(os.getcwd(), "venv", "bin", "yt-dlp")
        if os.path.exists(venv_path):
            yt_dlp_executable = venv_path
        else:
            yt_dlp_executable = "yt-dlp"  # Fallback to name and hope for the best

    cmd = [
        yt_dlp_executable,
        "-x",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "--no-playlist",
        "--socket-timeout", "30",
        "--max-filesize", "100m",
        "-o", output_path,
        url
    ]
    
    try:
        # Run yt-dlp as async subprocess (doesn't block FastAPI)
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait with timeout — don't let a single request hang the server
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=300  # 5 minute timeout
        )
        
        if process.returncode != 0:
            error_output = stderr.decode()
            
            # Parse common yt-dlp errors into user-friendly messages
            if "Private video" in error_output:
                raise ValueError(
                    "This video is private. Only public videos can be summarized."
                )
            elif "Video unavailable" in error_output:
                raise ValueError(
                    "This video is unavailable. It may have been deleted or "
                    "is geo-restricted in your region."
                )
            elif "Unsupported URL" in error_output:
                raise ValueError(
                    "This URL is not supported. Please provide a valid "
                    "YouTube, Vimeo, or other supported video URL."
                )
            elif "HTTP Error 429" in error_output:
                raise ValueError(
                    "Too many requests to the video platform. "
                    "Please wait a moment and try again."
                )
            else:
                logger.error(f"yt-dlp error: {error_output}")
                raise ValueError(
                    f"Failed to download video audio. Error: {error_output[:200]}"
                )
        
        # yt-dlp might add extensions, find the actual output file
        actual_path = _find_output_file(output_path, file_id)
        
        if not actual_path:
            raise ValueError("Audio download completed but output file not found.")
        
        # Convert to Whisper-optimal format: 16kHz mono WAV
        wav_path = await _convert_to_whisper_format(actual_path, file_id)
        
        # Clean up the original download if different from WAV
        if actual_path != wav_path and os.path.exists(actual_path):
            os.remove(actual_path)
        
        logger.info(f"Audio extracted successfully: {wav_path}")
        
        return {
            "audio_path": wav_path,
            "source": "url",
            "original_url": url,
        }
        
    except asyncio.TimeoutError:
        raise ValueError(
            "Video download timed out (5 minute limit). "
            "Try a shorter video or upload the file directly."
        )
    except ValueError:
        raise  # Re-raise our own errors
    except Exception as e:
        logger.error(f"Audio extraction from URL failed: {e}")
        raise ValueError(f"Failed to extract audio: {str(e)}")


async def extract_audio_from_file(file_path: str) -> dict:
    """
    Extract audio from an uploaded video file using FFmpeg.
    
    Args:
        file_path: Path to the uploaded video file
        
    Returns:
        dict with audio_path
        
    Raises:
        ValueError: If file has no audio or FFmpeg fails
    """
    _ensure_temp_dir()
    
    file_id = str(uuid.uuid4())[:8]
    
    logger.info(f"Extracting audio from uploaded file: {file_path}")
    
    wav_path = await _convert_to_whisper_format(file_path, file_id)
    
    return {
        "audio_path": wav_path,
        "source": "upload",
    }


async def _convert_to_whisper_format(input_path: str, file_id: str) -> str:
    """
    Convert any audio/video file to Whisper's optimal format:
    16kHz sample rate, mono channel, WAV format.
    
    WHY THESE SPECIFIC SETTINGS?
    - 16kHz: Whisper was trained on 16kHz audio. Higher sample rates
      don't improve accuracy but increase processing time.
    - Mono: Whisper processes single-channel audio. Stereo would just
      double the data without benefit.
    - WAV: Uncompressed format that Whisper reads directly. No decoding step.
    """
    output_path = os.path.join(TEMP_DIR, f"{file_id}_whisper.wav")
    
    # Try to find ffmpeg in PATH
    ffmpeg_executable = shutil.which("ffmpeg") or "ffmpeg"

    # FFmpeg command breakdown:
    # -i input     → input file
    # -ar 16000    → resample to 16kHz
    # -ac 1        → convert to mono (1 channel)
    # -y           → overwrite output if exists
    cmd = [
        ffmpeg_executable,
        "-i", input_path,
        "-ar", "16000",
        "-ac", "1",
        "-y",
        output_path
    ]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=120  # 2 minute timeout for conversion
        )
        
        if process.returncode != 0:
            error_output = stderr.decode()
            
            if "does not contain any stream" in error_output:
                raise ValueError(
                    "This file has no audio track. "
                    "Please upload a video/audio file with sound."
                )
            
            logger.error(f"FFmpeg error: {error_output[:500]}")
            raise ValueError("Failed to process audio. The file may be corrupted.")
        
        if not os.path.exists(output_path):
            raise ValueError("Audio conversion completed but output file not found.")
        
        file_size = os.path.getsize(output_path)
        logger.info(
            f"Audio converted to Whisper format: {output_path} "
            f"({file_size / 1024 / 1024:.1f} MB)"
        )
        
        return output_path
        
    except asyncio.TimeoutError:
        raise ValueError(
            "Audio conversion timed out. The file may be too large or corrupted."
        )
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"FFmpeg conversion failed: {e}")
        raise ValueError(f"Audio conversion failed: {str(e)}")


def _find_output_file(expected_path: str, file_id: str) -> Optional[str]:
    """
    Find the actual output file from yt-dlp.
    
    yt-dlp sometimes adds/changes extensions, so we search for files
    matching our file_id in the temp directory.
    """
    if os.path.exists(expected_path):
        return expected_path
    
    # Search for files with our file_id prefix
    for filename in os.listdir(TEMP_DIR):
        if filename.startswith(file_id):
            return os.path.join(TEMP_DIR, filename)
    
    return None


def cleanup_temp_files(*file_paths: str):
    """
    Remove temporary files. Called in finally blocks.
    
    WHY THIS IS CRITICAL:
    Every video request creates temp files. Without cleanup,
    your server's disk fills up and crashes. In production,
    this is a guaranteed incident if you forget.
    """
    for path in file_paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
                logger.debug(f"Cleaned up temp file: {path}")
            except Exception as e:
                logger.warning(f"Failed to clean up {path}: {e}")
