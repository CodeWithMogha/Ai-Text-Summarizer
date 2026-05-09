"""
AI Summarization Platform — FastAPI Application Entry Point

THIS IS YOUR SERVER'S FRONT DOOR.
Think of main.py like the receptionist at a building:
- It greets requests (CORS)
- It directs them to the right department (routers)
- It sets up the building before opening (startup events)
- It provides a map of the building (API docs at /docs)

STARTUP SEQUENCE:
1. Load environment variables from .env
2. Configure CORS (who's allowed to talk to this server)
3. Register routers (connect URL paths to handler functions)
4. On startup: load the Whisper model (do heavy work ONCE)
5. Start accepting requests
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load .env BEFORE importing anything that uses env vars
load_dotenv(override=True)

from routers import text, pdf, video
from services.transcriber import load_whisper_model
from utils.logger import logger


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LIFESPAN — runs code at startup and shutdown
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Code before `yield` runs at STARTUP.
    Code after `yield` runs at SHUTDOWN.
    
    WHY LOAD WHISPER HERE?
    Loading a neural network model takes 10-30 seconds.
    If we loaded it inside each request handler, EVERY user would
    wait an extra 30 seconds. By loading at startup, it's in memory
    and ready for instant use.
    
    ANALOGY: It's like pre-heating the oven before customers arrive
    at a restaurant, vs heating it when each order comes in.
    """
    # ── STARTUP ──────────────────────────────────────────────────
    logger.info("🚀 Starting AI Summarization Platform...")
    
    # Create temp directory for file processing
    temp_dir = os.getenv("TEMP_DIR", "./temp")
    os.makedirs(temp_dir, exist_ok=True)
    logger.info(f"Temp directory ready: {temp_dir}")
    
    # Verify Gemini API key is set
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.startswith("sk-your"):
        logger.warning(
            "⚠️  GEMINI_API_KEY not configured! "
            "Text/PDF/Video summarization will fallback to Free Mode. "
            "Set it in your .env file."
        )
    else:
        logger.info("✅ Gemini API key configured")
    
    # Load Whisper model (heavy operation — only once)
    try:
        load_whisper_model()
        logger.info("✅ Whisper model loaded")
    except Exception as e:
        logger.warning(
            f"⚠️  Whisper model failed to load: {e}. "
            "Video summarization will not work. "
            "Text and PDF summarization will still work."
        )
    
    logger.info("✅ AI Summarization Platform is ready!")
    
    yield  # Server is running and accepting requests
    
    # ── SHUTDOWN ─────────────────────────────────────────────────
    logger.info("Shutting down AI Summarization Platform...")
    
    # Clean up any remaining temp files
    temp_dir = os.getenv("TEMP_DIR", "./temp")
    if os.path.exists(temp_dir):
        for f in os.listdir(temp_dir):
            try:
                os.remove(os.path.join(temp_dir, f))
            except Exception:
                pass
    
    logger.info("Shutdown complete. Goodbye! 👋")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CREATE THE APP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

app = FastAPI(
    title="AI Summarization Platform",
    description=(
        "Summarize any text, PDF document, or video in seconds using AI. Powered by Google Gemini and OpenAI Whisper."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CORS MIDDLEWARE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# WHY CORS MATTERS:
# Your frontend runs on localhost:3000, backend on localhost:8000.
# Browsers block requests between different origins by default
# (it's a security feature). CORS tells the browser "it's okay,
# let localhost:3000 talk to localhost:8000."
#
# Without this, you'll see this error in the browser console:
# "Access to fetch at 'http://localhost:8000' from origin
#  'http://localhost:3000' has been blocked by CORS policy"
#
# COMMON MISTAKE: Setting allow_origins=["*"] in production.
# This lets ANY website call your API. In production, set it
# to your actual domain only.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REGISTER ROUTERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Each router handles a group of related endpoints:
# - /summarize/text     → text.py
# - /summarize/pdf      → pdf.py
# - /summarize/video/*  → video.py
#
# WHY SEPARATE ROUTERS?
# Same reason a restaurant has different chefs for different cuisines.
# Each file handles one type of input. Easy to find, easy to maintain.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

app.include_router(text.router, prefix="/api")
app.include_router(pdf.router, prefix="/api")
app.include_router(video.router, prefix="/api")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HEALTH CHECK ENDPOINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/")
async def root():
    """Health check — used by deployment platforms to verify the server is alive."""
    return {
        "status": "healthy",
        "service": "AI Summarization Platform",
        "version": "1.0.0",
        "endpoints": {
            "text": "/api/summarize/text",
            "pdf": "/api/summarize/pdf",
            "video_url": "/api/summarize/video/url",
            "video_upload": "/api/summarize/video/upload",
            "docs": "/docs",
        }
    }


@app.get("/health")
async def health_check():
    """Detailed health check for monitoring."""
    return {
        "status": "healthy",
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
        "whisper_model": os.getenv("WHISPER_MODEL", "base"),
    }
