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
import json
from datetime import datetime
import threading
import uuid
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SEPARATED_FOLDER'] = 'separated'

# Create folders
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
Path(app.config['SEPARATED_FOLDER']).mkdir(exist_ok=True)

# Store job status
jobs = {}


def generate_job_id():
    """Generate unique job ID"""
    return str(uuid.uuid4())[:8]


def run_download_and_separate(job_id, youtube_url):
    """Download from YouTube and separate audio"""
    try:
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
        result = subprocess.run(download_cmd, capture_output=True, text=True, timeout=600, cwd=os.getcwd())
        
        logger.info(f"Download stdout: {result.stdout}")
        logger.info(f"Download stderr: {result.stderr}")
        
        if result.returncode != 0:
            jobs[job_id] = {
                "status": "error",
                "message": f"Download failed: {result.stderr}"
            }
            return
        
        # Try to find the downloaded file
        audio_file = None
        
        # First, try to extract from stdout if script printed the path
        if result.stdout:
            for line in result.stdout.split('\n'):
                if line.startswith('/') or (len(line) > 2 and line[1] == ':'):  # Unix or Windows path
                    path_candidate = Path(line.strip())
                    if path_candidate.exists() and path_candidate.suffix == '.mp3':
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
        
        
        # Separate audio
        jobs[job_id] = {"status": "separating", "progress": 50, "message": "Separating audio..."}
        
        separate_cmd = [
            sys.executable, "separate_audio.py",
            audio_file,
            "-o", app.config['SEPARATED_FOLDER'],
            "-m", "mdx"  # Lighter model for cloud deployment
        ]
        
        logger.info(f"Running separation: {' '.join(separate_cmd)}")
        result = subprocess.run(separate_cmd, capture_output=True, text=True, timeout=600, cwd=os.getcwd())
        
        logger.info(f"Separation stdout: {result.stdout}")
        logger.info(f"Separation stderr: {result.stderr}")
        
        if result.returncode != 0:
            jobs[job_id] = {
                "status": "error",
                "message": f"Separation failed: {result.stderr}"
            }
            return
        
        # Find separated files
        separated_dir = Path(app.config['SEPARATED_FOLDER']) / "mdx"
        
        stems = {}
        for stem_dir in separated_dir.iterdir():
            if stem_dir.is_dir():
                for wav_file in stem_dir.glob("*.wav"):
                    stem_name = wav_file.stem
                    stems[stem_name] = str(wav_file)
        
        jobs[job_id] = {
            "status": "completed",
            "progress": 100,
            "message": "Successfully separated audio!",
            "stems": stems,
            "original_file": audio_file
        }
        
    except subprocess.TimeoutExpired:
        jobs[job_id] = {"status": "error", "message": "Processing timeout - file may be too long"}
        logger.error(f"Timeout for job {job_id}")
    except Exception as e:
        jobs[job_id] = {"status": "error", "message": f"Error: {str(e)}"}
        logger.error(f"Error in job {job_id}: {str(e)}", exc_info=True)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "app": "Voice Extraction Studio"}), 200


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
