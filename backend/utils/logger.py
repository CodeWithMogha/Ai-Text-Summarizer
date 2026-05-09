"""
AI Summarization Platform — Structured Logging Utility

WHY THIS EXISTS:
When your app crashes at 3 AM in production, print() statements won't help you.
Structured logs with timestamps, levels, and context are how real engineers debug.
Think of this as your app's flight recorder — it captures everything.
"""

import logging
import sys
from datetime import datetime


def setup_logger(name: str = "ai_summarizer") -> logging.Logger:
    """
    Create a production-grade logger with structured formatting.
    
    Why structured logging matters:
    - Timestamps tell you WHEN something happened
    - Log levels let you filter noise (DEBUG in dev, WARNING in prod)
    - Module names tell you WHERE in the code the log came from
    - Consistent format makes logs parseable by tools like DataDog, Splunk
    """
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Console handler — writes to stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # Format: [2024-03-15 14:30:22] [INFO] [summarizer] Processing 5 chunks
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


# Create a default logger instance that any module can import
logger = setup_logger()
