#!/usr/bin/env python3
"""
Voice Extraction Web App
Mobile-friendly Flask app for downloading and separating audio
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import subprocess
from datetime import datetime, timedelta
import threading
import uuid
import logging
import time

# Suppress warnings
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore'

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SEPARATED_FOLDER'] = 'separated'
app.config['CLEANUP_MAX_AGE_HOURS'] = int(os.environ.get('CLEANUP_MAX_AGE_HOURS', '6'))
app.config['MODEL_NAME'] = os.environ.get('DEMUCS_MODEL', 'mdx')

# Create folders
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
Path(app.config['SEPARATED_FOLDER']).mkdir(exist_ok=True)

# Store job status
jobs = {}

ALLOWED_AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.webm', '.ogg', '.flac', '.aac'}


def child_process_env():
    """Force UTF-8 in child Python scripts on Windows."""
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        import imageio_ffmpeg

        ffmpeg_dir = str(Path(imageio_ffmpeg.get_ffmpeg_exe()).parent)
        env["PATH"] = ffmpeg_dir + os.pathsep + env.get("PATH", "")
    except Exception:
        pass

    return env


def process_error_message(label, result):
    """Return a browser-friendly error without dumping a full traceback."""
    details = "\n".join(
        part.strip() for part in (result.stderr, result.stdout) if part and part.strip()
    )
    if not details:
        return f"{label} failed"

    if "ffprobe and ffmpeg not found" in details or "ffmpeg not found" in details.lower():
        return f"{label} failed: FFmpeg is not installed or not available to Python."

    if "CERTIFICATE_VERIFY_FAILED" in details:
        return (
            f"{label} failed: local SSL certificate verification failed. "
            "The downloader retried with certificate bypass, but YouTube still could not be reached."
        )

    if "Sign in to confirm" in details or "not a bot" in details:
        return (
            f"{label} failed: YouTube is asking for bot verification on this cloud server. "
            "Upload the audio file instead, or try another video later."
        )

    if "HTTP Error 429" in details or "Too Many Requests" in details:
        return f"{label} failed: YouTube is rate limiting this connection. Wait and try again later."

    lines = [line.strip() for line in details.splitlines() if line.strip()]
    if "Traceback (most recent call last)" in details and lines:
        return f"{label} failed: {lines[-1]}"

    return f"{label} failed: {details[-1200:]}"


def generate_job_id():
    """Generate unique job ID"""
    return str(uuid.uuid4())[:8]


def is_allowed_audio_file(filename):
    """Return True when an uploaded filename looks like a supported audio file."""
    return Path(filename).suffix.lower() in ALLOWED_AUDIO_EXTENSIONS


def safe_uploaded_audio_name(job_id, filename):
    """Build a filesystem-safe upload name while preserving the audio extension."""
    suffix = Path(filename).suffix.lower()
    safe_name = secure_filename(filename)
    safe_stem = Path(safe_name).stem or "audio"
    return f"{job_id}_{safe_stem}{suffix}"


def cleanup_old_files():
    """Remove old generated files to keep cloud disks from filling up."""
    max_age = timedelta(hours=app.config['CLEANUP_MAX_AGE_HOURS'])
    cutoff = datetime.now() - max_age

    for folder_name in (app.config['UPLOAD_FOLDER'], app.config['SEPARATED_FOLDER']):
        root = Path(folder_name)
        if not root.exists():
            continue

        for file_path in root.rglob('*'):
            if not file_path.is_file():
                continue

            modified = datetime.fromtimestamp(file_path.stat().st_mtime)
            if modified < cutoff:
                try:
                    file_path.unlink()
                except OSError:
                    logger.warning("Could not remove old file: %s", file_path)

        for dir_path in sorted((p for p in root.rglob('*') if p.is_dir()), reverse=True):
            try:
                dir_path.rmdir()
            except OSError:
                pass


def cleanup_loop():
    interval = int(os.environ.get('CLEANUP_INTERVAL_SECONDS', '1800'))
    while True:
        time.sleep(interval)
        cleanup_old_files()


cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
cleanup_thread.start()


def run_separate_audio(job_id, audio_file, progress=50):
    """Separate a local audio file and update job status with generated stems."""
    jobs[job_id] = {"status": "separating", "progress": progress, "message": "Separating audio..."}

    model_name = app.config['MODEL_NAME']
    separate_cmd = [
        sys.executable, "separate_audio.py",
        audio_file,
        "-o", app.config['SEPARATED_FOLDER'],
        "-m", model_name
    ]

    logger.info(f"Running separation: {' '.join(separate_cmd)}")
    result = subprocess.run(
        separate_cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
        cwd=os.getcwd(),
        env=child_process_env()
    )

    logger.info(f"Separation stdout: {result.stdout}")
    logger.info(f"Separation stderr: {result.stderr}")

    if result.returncode != 0:
        jobs[job_id] = {
            "status": "error",
            "message": process_error_message("Separation", result)
        }
        return

    separated_dir = Path(app.config['SEPARATED_FOLDER']) / model_name / Path(audio_file).stem

    stems = {}
    if not separated_dir.exists():
        jobs[job_id] = {
            "status": "error",
            "message": "Separated audio folder was not created"
        }
        return

    for wav_file in separated_dir.glob("*.wav"):
        stem_name = wav_file.stem
        stems[stem_name] = str(wav_file)

    jobs[job_id] = {
        "status": "completed",
        "progress": 100,
        "message": "Successfully separated audio!",
        "stems": stems,
        "original_file": audio_file
    }


def run_download_and_separate(job_id, youtube_url):
    """Download from YouTube and separate audio"""
    try:
        cleanup_old_files()
        jobs[job_id] = {"status": "downloading", "progress": 0, "message": "Downloading audio..."}
        
        # Create output directory
        upload_dir = Path(app.config['UPLOAD_FOLDER'])
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Download audio with full path
        download_cmd = [
            sys.executable, "download_audio.py",
            youtube_url,
            "-o", str(upload_dir)
        ]
        
        logger.info(f"Running download: {' '.join(download_cmd)}")
        # Increased timeout to 15 minutes (900s) for exponential backoff retries
        result = subprocess.run(
            download_cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=900,
            cwd=os.getcwd(),
            env=child_process_env()
        )
        
        logger.info(f"Download stdout: {result.stdout}")
        logger.info(f"Download stderr: {result.stderr}")
        
        if result.returncode != 0:
            jobs[job_id] = {
                "status": "error",
                "message": process_error_message("Download", result)
            }
            return
        
        # Try to find the downloaded file
        audio_file = None
        
        # First, try to extract from stdout if script printed the path
        if result.stdout:
            for line in result.stdout.split('\n'):
                line = line.strip()
                if not line:
                    continue

                path_candidate = Path(line)
                if not path_candidate.is_absolute():
                    path_candidate = Path.cwd() / path_candidate

                if path_candidate.exists() and path_candidate.suffix.lower() == '.mp3':
                    audio_file = str(path_candidate)
                    logger.info(f"Found file from stdout: {audio_file}")
                    break
        
        # If not found, search directory
        if not audio_file:
            uploaded_files = list(upload_dir.glob("**/*.mp3"))
            if uploaded_files:
                audio_file = str(max(uploaded_files, key=lambda p: p.stat().st_mtime))
                logger.info(f"Found file from directory search: {audio_file}")
        
        if not audio_file:
            logger.error(f"No MP3 found. Contents of {upload_dir}: {list(upload_dir.glob('*'))}")
            jobs[job_id] = {"status": "error", "message": "No audio file found after download"}
            return
        
        run_separate_audio(job_id, audio_file, progress=50)
        
    except subprocess.TimeoutExpired:
        jobs[job_id] = {"status": "error", "message": "Processing timeout - file may be too long"}
        logger.error(f"Timeout for job {job_id}")
    except Exception as e:
        jobs[job_id] = {"status": "error", "message": f"Error: {str(e)}"}
        logger.error(f"Error in job {job_id}: {str(e)}", exc_info=True)


def run_upload_and_separate(job_id, audio_file):
    """Separate an already uploaded audio file."""
    try:
        cleanup_old_files()
        run_separate_audio(job_id, audio_file, progress=10)
    except subprocess.TimeoutExpired:
        jobs[job_id] = {"status": "error", "message": "Processing timeout - file may be too long"}
        logger.error(f"Timeout for job {job_id}")
    except Exception as e:
        jobs[job_id] = {"status": "error", "message": f"Error: {str(e)}"}
        logger.error(f"Error in uploaded job {job_id}: {str(e)}", exc_info=True)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "app": "Voice Extraction Studio",
        "model": app.config['MODEL_NAME']
    }), 200


@app.route('/')
def index():
    """Serve main page"""
    return render_template('index.html')


@app.route('/api/download', methods=['POST'])
def download():
    """Start download and separation job"""
    data = request.json
    youtube_url = data.get('url', '').strip()
    
    if not youtube_url:
        return jsonify({"error": "No URL provided"}), 400
    
    job_id = generate_job_id()
    
    # Start processing in background
    thread = threading.Thread(
        target=run_download_and_separate,
        args=(job_id, youtube_url)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({"job_id": job_id})


@app.route('/api/upload', methods=['POST'])
def upload_audio():
    """Start separation job from an uploaded audio file."""
    uploaded_file = request.files.get('audio')

    if not uploaded_file or not uploaded_file.filename:
        return jsonify({"error": "No audio file uploaded"}), 400

    if not is_allowed_audio_file(uploaded_file.filename):
        allowed = ", ".join(sorted(ext.lstrip('.') for ext in ALLOWED_AUDIO_EXTENSIONS))
        return jsonify({"error": f"Unsupported audio file. Use one of: {allowed}"}), 400

    job_id = generate_job_id()
    upload_dir = Path(app.config['UPLOAD_FOLDER'])
    upload_dir.mkdir(parents=True, exist_ok=True)
    audio_path = upload_dir / safe_uploaded_audio_name(job_id, uploaded_file.filename)
    uploaded_file.save(audio_path)

    jobs[job_id] = {"status": "queued", "progress": 0, "message": "Upload received..."}

    thread = threading.Thread(
        target=run_upload_and_separate,
        args=(job_id, str(audio_path))
    )
    thread.daemon = True
    thread.start()

    return jsonify({"job_id": job_id})


@app.route('/api/status/<job_id>', methods=['GET'])
def status(job_id):
    """Get job status"""
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    
    return jsonify(jobs[job_id])


@app.route('/api/download-stem/<job_id>/<stem_name>', methods=['GET'])
def download_stem(job_id, stem_name):
    """Download a separated stem"""
    if job_id not in jobs or jobs[job_id].get('status') != 'completed':
        return jsonify({"error": "Job not found or not completed"}), 404
    
    stems = jobs[job_id].get('stems', {})
    if stem_name not in stems:
        return jsonify({"error": "Stem not found"}), 404
    
    file_path = stems[stem_name]
    return send_file(file_path, as_attachment=True, download_name=f"{stem_name}.wav")


@app.route('/api/stream-stem/<job_id>/<stem_name>', methods=['GET'])
def stream_stem(job_id, stem_name):
    """Stream a separated stem for playback"""
    if job_id not in jobs or jobs[job_id].get('status') != 'completed':
        return jsonify({"error": "Job not found or not completed"}), 404
    
    stems = jobs[job_id].get('stems', {})
    if stem_name not in stems:
        return jsonify({"error": "Stem not found"}), 404
    
    file_path = stems[stem_name]
    return send_file(file_path, mimetype='audio/wav')


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal error: {error}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
