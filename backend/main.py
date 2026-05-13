"""FastAPI application entry point."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv(override=True)

from routers import text, pdf, video
from services.transcriber import load_whisper_model
from utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("🚀 Starting AI Summarization Platform...")

    temp_dir = os.getenv("TEMP_DIR", "./temp")
    os.makedirs(temp_dir, exist_ok=True)
    logger.info(f"Temp directory ready: {temp_dir}")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.startswith("sk-your"):
        logger.warning("⚠️  GEMINI_API_KEY not configured! Summarization will use Free Mode.")
    else:
        logger.info("✅ Gemini API key configured")

    try:
        load_whisper_model()
        logger.info("✅ Whisper model loaded")
    except Exception as e:
        logger.warning(f"⚠️  Whisper model failed to load: {e}. Video summarization unavailable.")

    logger.info("✅ AI Summarization Platform is ready!")

    yield

    logger.info("Shutting down AI Summarization Platform...")
    temp_dir = os.getenv("TEMP_DIR", "./temp")
    if os.path.exists(temp_dir):
        for f in os.listdir(temp_dir):
            try:
                os.remove(os.path.join(temp_dir, f))
            except Exception:
                pass
    logger.info("Shutdown complete. 👋")


app = FastAPI(
    title="AI Summarization Platform",
    description="Summarize any text, PDF document, or video using AI.",
    version="1.0.0",
    lifespan=lifespan,
)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(text.router, prefix="/api")
app.include_router(pdf.router, prefix="/api")
app.include_router(video.router, prefix="/api")


@app.get("/")
async def root():
    """Health check endpoint."""
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
    """Detailed health check."""
    return {
        "status": "healthy",
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
        "whisper_model": os.getenv("WHISPER_MODEL", "base"),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
