FROM python:3.11-slim

# Install system dependencies: FFmpeg for audio processing, git for yt-dlp
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for Docker layer caching
# (dependencies change less often than code)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create temp directory for file processing
RUN mkdir -p /app/temp

# Expose port
EXPOSE 8000

# Run with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
