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

# Pre-download the demucs model to avoid timeout during runtime
RUN python -c "from demucs.pretrained import get_model; get_model('mdx')" || true

# Expose port
EXPOSE 5000

# Set environment
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Run the app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "300", "--workers", "1", "app:app"]
