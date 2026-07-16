# Online Deployment Guide

Voice Extraction Studio needs a real backend server. It cannot be hosted as a static site because it runs `yt-dlp`, FFmpeg, PyTorch, and Demucs.

The recommended online path is Docker deployment on Railway, Render, Fly.io, or a VPS. Railway is the default target for this project because `Dockerfile` and `railway.toml` are included.

## What Is Already Prepared

- `Dockerfile` installs FFmpeg, Deno, Python dependencies, and preloads the `mdx` Demucs model when possible.
- `railway.toml` tells Railway to build with Docker and use `/health` as the health check.
- `app.py` uses one Gunicorn worker and in-memory job state.
- The web app can process either a YouTube URL or a directly uploaded audio file.
- Old generated files are cleaned automatically using:
  - `CLEANUP_MAX_AGE_HOURS`, default `6`
  - `CLEANUP_INTERVAL_SECONDS`, default `1800`
- The active Demucs model is controlled with `DEMUCS_MODEL`, default `mdx`.
- Demucs model files are cached into `DEMUCS_MODEL_REPO` during Docker build.

## Deploy To Railway

1. Push this project to a GitHub repository.

2. Open Railway and create a new project from the GitHub repository.

3. Railway should detect the `Dockerfile`. The included `railway.toml` also sets the builder to Docker.

4. After deploy, open the generated Railway domain.

5. Check health:

   ```text
   https://YOUR-APP.up.railway.app/health
   ```

## Suggested Railway Settings

Use a paid/resource-capable service for real separation work. Demucs is CPU and memory heavy, and free/small instances may timeout or restart.

Suggested environment variables:

```text
DEMUCS_MODEL=mdx
DEMUCS_MODEL_REPO=/app/model_repo
DEMUCS_SHIFTS=0
DEMUCS_SEGMENT=20
DEMUCS_OVERLAP=0.1
DEMUCS_JOBS=0
SEPARATION_TIMEOUT_SECONDS=1200
CLEANUP_MAX_AGE_HOURS=6
CLEANUP_INTERVAL_SECONDS=1800
PYTHONUTF8=1
PYTHONIOENCODING=utf-8
```

## Local Docker Test

If Docker is installed:

```powershell
docker build -t voice-extraction .
docker run --rm -p 5000:5000 voice-extraction
```

Then open:

```text
http://127.0.0.1:5000
```

## Important Limits

- The first build/run can take a while because PyTorch and Demucs are large.
- The Docker image can become large after model caching.
- Model downloads happen during Docker build. If model caching fails, the deploy should fail instead of surprising users during separation.
- YouTube may occasionally block or rate-limit cloud IP addresses. Use direct audio upload when that happens.
- Generated audio files are temporary and will be deleted by cleanup.
- With the current in-memory job state, keep Gunicorn at one worker.

## If You Need A Stronger Online Version

For heavier public use, the next architecture should split the app into:

- Flask web frontend/API
- Background worker for separation jobs
- Redis or database for job state
- Persistent object storage for stems

The current version is good for personal or small private use online.
