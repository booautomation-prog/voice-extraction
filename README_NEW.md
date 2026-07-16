# YouTube Audio Downloader & Voice Extraction Studio

Simple Python tools for downloading audio from YouTube and separating vocals, drums, and instruments. Includes a mobile-friendly web app!

## Quick Start

### Portable Windows Copy

To copy this project to another Windows computer, see [PORTABLE_WINDOWS.md](PORTABLE_WINDOWS.md).

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Command Line Tools

#### Download Audio
```bash
python download_audio.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

#### Separate Audio
```bash
python separate_audio.py "downloads/song_name.mp3"
```

## 🌐 Web App (Mobile-Friendly)

### Run Locally
```bash
python app.py
```

Then open: **http://localhost:5000**

### Features
- ✅ Download audio from YouTube
- ✅ Separate into vocals, drums, bass, and other instruments
- ✅ Play/preview each stem
- ✅ Toggle channels on/off
- ✅ Download individual stems
- ✅ Mobile-responsive design

### Deploy to Cloud
For cloud deployment (Railway, Heroku, etc.), see [DEPLOYMENT.md](DEPLOYMENT.md)

## Setup

### 1. Install FFmpeg
The script requires FFmpeg to convert audio formats.

**Windows:**
```powershell
# Using winget (Windows 11)
winget install ffmpeg

# Or using chocolatey
choco install ffmpeg

# Or download from: https://ffmpeg.org/download.html
```

**Mac:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt-get install ffmpeg
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

## 📥 Command Line Usage

### Download a single video
```bash
python download_audio.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Download to a specific folder
```bash
python download_audio.py "https://www.youtube.com/watch?v=VIDEO_ID" -o my_music
```

### Download multiple videos from a file
Create a `urls.txt` file with one URL per line:
```
https://www.youtube.com/watch?v=VIDEO_ID_1
https://www.youtube.com/watch?v=VIDEO_ID_2
https://www.youtube.com/watch?v=VIDEO_ID_3
```

Then run:
```bash
python download_audio.py -f urls.txt
```

## 🎵 Source Separation

### Separate Vocals, Drums, and Instruments

Once you've downloaded audio, you can separate it into different components (vocals, drums, bass, other).

```bash
# Separate with default model (recommended)
python separate_audio.py "downloads/song_name.mp3"

# Specify output directory
python separate_audio.py "downloads/song_name.mp3" -o my_stems

# Use different model (faster or higher quality)
python separate_audio.py "downloads/song_name.mp3" --model mdx
```

**Available Models:**
- `htdemucs` (default) - Best quality, recommended
- `mdx` - Faster, good quality
- `mdx_extra` - Highest quality, slowest
- `htdemucs_ft` - Fine-tuned on various datasets

**Output:** Separates audio into:
- `vocals.wav` - Lead vocals/singing
- `drums.wav` - Drum tracks
- `bass.wav` - Bass instrument
- `other.wav` - Other instruments

## Command Line Options

### download_audio.py
- `url` - YouTube URL (required unless using `-f`)
- `-o, --output` - Output directory (default: `downloads`)
- `-f, --file` - Text file with multiple URLs (one per line)

### separate_audio.py
- `audio_file` - Audio file to separate
- `-o, --output` - Output directory (default: `separated`)
- `-m, --model` - Model to use (default: `htdemucs`)
- `--list-models` - List available models

## 💡 Example Workflow

```bash
# Download a song
python download_audio.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Separate it
python separate_audio.py "downloads/Never Gonna Give You Up.mp3"

# Use the stems in your DAW or music project
# Find them in: separated/htdemucs/Never Gonna Give You Up/
```

## 📱 Web App Example

1. Open **http://localhost:5000** on your phone
2. Paste a YouTube URL
3. Click "Download & Separate"
4. Wait for processing to complete (~2-3 minutes per song)
5. Preview each stem and toggle channels
6. Download individual stems as needed

## 📂 Project Structure

```
voice-extraction/
├── app.py                 # Flask web app
├── download_audio.py      # YouTube downloader
├── separate_audio.py      # Audio separation tool
├── requirements.txt       # Dependencies
├── README.md             # This file
├── DEPLOYMENT.md         # Cloud deployment guide
├── templates/
│   └── index.html        # Web UI
└── static/
    ├── style.css         # Styling
    └── script.js         # Frontend logic
```

## ⚙️ Notes

- Downloaded files are saved as MP3 format (192 kbps)
- Filenames are based on YouTube video titles
- The script requires internet connection
- Source separation requires GPU for faster processing (uses CPU if GPU not available)
- First run downloads the Demucs model (~500MB)
- Processing time: ~2-3 minutes per song (varies by audio length)

## 🔧 Troubleshooting

**FFmpeg not found:**
- Make sure FFmpeg is installed and in PATH
- Restart terminal after installation

**Model download fails:**
- Check internet connection
- Model is ~500MB, may take time
- Try again later if connection is slow

**Slow processing:**
- Install PyTorch with GPU support for faster separation
- Shorter songs process faster
- Free cloud tiers may have slower processors

**Web app won't start:**
- Make sure Flask is installed: `pip install flask`
- Check if port 5000 is available
- Try a different port: `python app.py --port 8000`

**"Timeout" on cloud deployment:**
- Long songs may timeout on free cloud tiers
- Try with shorter songs (< 5 minutes) first
- Upgrade to paid tier for production use

## 📦 Dependencies

- `yt-dlp` - YouTube downloader
- `demucs` - Audio source separation
- `torch` & `torchaudio` - Deep learning framework
- `flask` - Web framework
- `ffmpeg` - Audio processing

## 📄 License

MIT

## 🤝 Contributing

Suggestions and improvements welcome!
