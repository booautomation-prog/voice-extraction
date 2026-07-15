# YouTube Audio Downloader

Simple Python script to download audio from YouTube URLs and convert to MP3.

## Setup

### 1. Install FFmpeg
The script requires FFmpeg to convert audio formats.

**Windows:**
```powershell
# Using chocolatey
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

## Usage

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

## Options

- `url` - YouTube URL (required unless using `-f`)
- `-o, --output` - Output directory (default: `downloads`)
- `-f, --file` - Text file with multiple URLs (one per line)

## Example

```bash
# Single download
python download_audio.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Batch download with custom folder
python download_audio.py -f my_playlist.txt -o audio_files
```

## Source Separation

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

## Notes

- Downloaded files are saved as MP3 format
- Audio quality is set to 192 kbps (adjustable in script)
- Filenames are based on YouTube video titles
- The script requires internet connection
- Source separation requires GPU for faster processing (uses CPU if GPU not available)
