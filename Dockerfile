FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including deno for JavaScript extraction
RUN apt-get update && apt-get install -y \
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
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Set environment variables
ENV HF_HUB_DISABLE_SYMLINKS_WARNING=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/root/.deno/bin:$PATH"

# Pre-download the demucs model during build
RUN mkdir -p /root/.cache/huggingface/hub && \
    python -c "from demucs.pretrained import get_model; get_model('mdx')" || echo "Model caching attempted"

# Expose port
EXPOSE 5000

# Set Flask app
ENV FLASK_APP=app.py

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "300", "--workers", "1", "--max-requests", "100", "app:app"]
