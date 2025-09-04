# Python base (Debian) so we can apt-get ffmpeg
FROM python:3.11-slim

# System deps (ffmpeg + runtime basics)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
  && rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app

# Install Python deps first (use cache)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . /app

# Ensure videos dir exists inside container
RUN mkdir -p /app/videos

# Default envs (can be overridden by docker-compose)
ENV BASE_URL="http://localhost:5000" \
    VIDEOS_DIR="/app/videos" \
    REDIS_URL="redis://redis:6379/0" \
    PYTHONUNBUFFERED=1