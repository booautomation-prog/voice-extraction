FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including deno for JavaScript extraction
RUN apt-get update && apt-get install -y \
    ca-certificates \
    ffmpeg \
    git \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install deno (required for yt-dlp YouTube extraction)
RUN curl -fsSL https://deno.land/x/install/install.sh | sh && \
    mv /root/.deno/bin/deno /usr/local/bin/

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Set environment variables
ENV HF_HUB_DISABLE_SYMLINKS_WARNING=1
ENV HF_HOME=/app/model_cache/huggingface
ENV TORCH_HOME=/app/model_cache/torch
ENV XDG_CACHE_HOME=/app/model_cache
ENV DEMUCS_MODEL=mdx
ENV CLEANUP_MAX_AGE_HOURS=6
ENV CLEANUP_INTERVAL_SECONDS=1800
ENV PYTHONUNBUFFERED=1
ENV PYTHONUTF8=1
ENV PYTHONIOENCODING=utf-8
ENV PATH="/root/.deno/bin:$PATH"

# Pre-download the demucs model during build
RUN mkdir -p /app/model_cache/huggingface /app/model_cache/torch && \
    python -c "from demucs.pretrained import get_model; get_model('mdx')" || echo "Model caching attempted"

# Expose port
EXPOSE 5000

# Set Flask app
ENV FLASK_APP=app.py

# Run with gunicorn
# Increased timeout to 900s (15 minutes) for YouTube retries with exponential backoff
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --timeout 900 --workers 1 --max-requests 100 app:app"]
