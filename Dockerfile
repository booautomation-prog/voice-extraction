FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Set environment variables for Hugging Face
ENV HF_HUB_DISABLE_SYMLINKS_WARNING=1
ENV PYTHONUNBUFFERED=1

# Pre-download the demucs model to cache during build
RUN mkdir -p /root/.cache/huggingface/hub && \
    python -c "from demucs.pretrained import get_model; get_model('mdx')" || echo "Model download attempted"

# Expose port
EXPOSE 5000

# Set Flask app
ENV FLASK_APP=app.py

# Run the app with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "300", "--workers", "1", "--max-requests", "100", "app:app"]
