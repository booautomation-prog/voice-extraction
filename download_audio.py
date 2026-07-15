#!/usr/bin/env python3
"""
YouTube Audio Downloader
Downloads audio from YouTube URLs and saves as MP3
"""

import os
import sys
import argparse
from pathlib import Path
from yt_dlp import YoutubeDL


def download_audio(url, output_dir="downloads"):
    """
    Download audio from a YouTube URL and save as MP3
    
    Args:
        url (str): YouTube URL
        output_dir (str): Directory to save the audio file
    
    Returns:
        str: Path to downloaded file or None if failed
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Configure yt-dlp options with explicit output format
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': str(output_path / '%(title)s'),  # Don't include extension - yt-dlp adds it
        'quiet': False,
        'no_warnings': False,
        'progress_hooks': [progress_hook],
    }
    
    try:
        print(f"Downloading audio from: {url}")
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # Get the actual filename that was created
            base_name = ydl.prepare_filename(info)
            mp3_name = Path(base_name).stem + ".mp3"
            audio_path = output_path / mp3_name
            
            if audio_path.exists():
                print(f"✓ Successfully downloaded: {audio_path.name}")
                return str(audio_path)
            else:
                # Fallback: search for the most recent MP3
                mp3_files = list(output_path.glob("*.mp3"))
                if mp3_files:
                    latest = max(mp3_files, key=lambda p: p.stat().st_mtime)
                    print(f"✓ Successfully downloaded: {latest.name}")
                    return str(latest)
                else:
                    print(f"✗ Error: File not found at {audio_path}", file=sys.stderr)
                    return None
    except Exception as e:
        print(f"✗ Error downloading audio: {e}", file=sys.stderr)
        return None


def progress_hook(d):
    """Progress hook for yt-dlp"""
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', 'N/A')
        speed = d.get('_speed_str', 'N/A')
        eta = d.get('_eta_str', 'N/A')
        print(f"Downloading: {percent} at {speed} ETA: {eta}", end='\r')


def main():
    parser = argparse.ArgumentParser(
        description='Download audio from YouTube URLs'
    )
    parser.add_argument(
        'url',
        help='YouTube URL to download'
    )
    parser.add_argument(
        '-o', '--output',
        default='downloads',
        help='Output directory (default: downloads)'
    )
    parser.add_argument(
        '-f', '--file',
        help='Text file containing multiple URLs (one per line)'
    )
    
    args = parser.parse_args()
    
    if args.file:
        # Download from multiple URLs in a file
        try:
            with open(args.file, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
            print(f"Found {len(urls)} URLs to download\n")
            for i, url in enumerate(urls, 1):
                print(f"[{i}/{len(urls)}]")
                result = download_audio(url, args.output)
                if result:
                    print(f"Saved: {result}\n")
                else:
                    print(f"Failed to download URL: {url}\n")
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found", file=sys.stderr)
            return 1
    else:
        # Download single URL
        result = download_audio(args.url, args.output)
        if not result:
            return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
