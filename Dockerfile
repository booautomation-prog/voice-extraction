FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including deno for JavaScript extraction
RUN apt-get update && apt-get install -y \
    build-essential \
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

# Install CPU-only PyTorch first so Railway does not pull CUDA/GPU wheels.
RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu \
        torch==2.3.1+cpu torchaudio==2.3.1+cpu && \
    python -m pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Set environment variables
ENV HF_HUB_DISABLE_SYMLINKS_WARNING=1
ENV HF_HOME=/app/model_cache/huggingface
ENV TORCH_HOME=/app/model_cache/torch
ENV XDG_CACHE_HOME=/app/model_cache
ENV DEMUCS_MODEL=6b9c2ca1
ENV DEMUCS_MODEL_REPO=/app/model_repo
ENV DEMUCS_SHIFTS=0
ENV DEMUCS_SEGMENT=1
ENV DEMUCS_OVERLAP=0
ENV DEMUCS_JOBS=0
ENV SEPARATION_TIMEOUT_SECONDS=1200
ENV CLEANUP_MAX_AGE_HOURS=6
ENV CLEANUP_INTERVAL_SECONDS=1800
ENV PYTHONUNBUFFERED=1
ENV PYTHONUTF8=1
ENV PYTHONIOENCODING=utf-8
ENV PATH="/root/.deno/bin:$PATH"

# Pre-download the Demucs model during build so public jobs do not hit
# Hugging Face or remote model downloads at runtime.
RUN mkdir -p /app/model_cache/huggingface /app/model_cache/torch /app/model_repo && \
    python cache_demucs_model.py "$DEMUCS_MODEL" "$DEMUCS_MODEL_REPO"

# Expose port
EXPOSE 5000

# Set Flask app
ENV FLASK_APP=app.py

# Run with gunicorn
# Increased timeout to 900s (15 minutes) for YouTube retries with exponential backoff
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --timeout 900 --workers 1 --max-requests 100 app:app"]
