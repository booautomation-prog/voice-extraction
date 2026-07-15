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
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Configure yt-dlp options
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
    }
    
    try:
        print(f"Downloading audio from: {url}")
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            base_filename = os.path.splitext(filename)[0]
            audio_filename = f"{base_filename}.mp3"
            print(f"✓ Successfully downloaded: {audio_filename}")
            return audio_filename
    except Exception as e:
        print(f"✗ Error downloading audio: {e}", file=sys.stderr)
        return None


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
                download_audio(url, args.output)
                print()
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found", file=sys.stderr)
            return 1
    else:
        # Download single URL
        download_audio(args.url, args.output)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
