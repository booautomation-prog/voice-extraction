#!/usr/bin/env python3
"""
YouTube Audio Downloader
Downloads audio from YouTube URLs and saves as MP3
"""

import os
import sys
import time
import json
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
    
    # Check cache first to avoid repeated YouTube requests
    cache_dir = Path("cache")
    cache_dir.mkdir(exist_ok=True)
    
    # Create cache key from URL
    import hashlib
    cache_key = hashlib.md5(url.encode()).hexdigest()
    cache_file = cache_dir / f"{cache_key}.json"
    
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
                cached_path = cache_data.get('path')
                if cached_path and Path(cached_path).exists():
                    print(f"Using cached download: {Path(cached_path).name}")
                    return cached_path
        except:
            pass  # Ignore cache errors, proceed with download
    
    # Configure yt-dlp options with enhanced bot bypass
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': str(output_path / '%(title)s'),
        'quiet': False,
        'no_warnings': False,
        'progress_hooks': [progress_hook],
        # Enhanced browser headers (looks like Chrome on Windows)
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        },
        # Retry with exponential backoff
        'socket_timeout': 30,
        'retries': 10,  # More retries with longer waits
        'fragment_retries': 10,
        # Wait between retries (will use exponential backoff)
        'default_search': 'ytsearch',
        # Use deno for JavaScript extraction
        'compat_opts': {'youtube.skip_unavailable_videos': True},
        # Network optimization
        'noprogress': False,
        'no_color': False,
    }
    
    # Retry loop with exponential backoff
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"Downloading audio from: {url}")
            print("(This may take a minute...)")
            
            with YoutubeDL(ydl_opts) as ydl:
                # Extract video info first to ensure we can access it
                print("Fetching video information...")
                info = ydl.extract_info(url, download=False)
                print(f"Found video: {info.get('title', 'Unknown')}")
                
                # Now download
                print("Downloading...")
                info = ydl.extract_info(url, download=True)
                
                # Get the actual filename that was created
                base_name = ydl.prepare_filename(info)
                mp3_name = Path(base_name).stem + ".mp3"
                audio_path = output_path / mp3_name
                
                if audio_path.exists():
                    print(f"✓ Successfully downloaded: {audio_path.name}")
                    
                    # Cache the result
                    try:
                        with open(cache_file, 'w') as f:
                            json.dump({
                                'url': url,
                                'path': str(audio_path),
                                'title': info.get('title', 'Unknown'),
                                'timestamp': time.time()
                            }, f)
                    except:
                        pass  # Ignore cache write errors
                    
                    return str(audio_path)
                else:
                    # Fallback: search for the most recent MP3
                    mp3_files = list(output_path.glob("*.mp3"))
                    if mp3_files:
                        latest = max(mp3_files, key=lambda p: p.stat().st_mtime)
                        print(f"✓ Successfully downloaded: {latest.name}")
                        
                        # Cache the result
                        try:
                            with open(cache_file, 'w') as f:
                                json.dump({
                                    'url': url,
                                    'path': str(latest),
                                    'title': info.get('title', 'Unknown'),
                                    'timestamp': time.time()
                                }, f)
                        except:
                            pass
                        
                        return str(latest)
                    else:
                        print(f"✗ Error: File not found at {audio_path}", file=sys.stderr)
                        return None
                        
        except Exception as e:
            error_msg = str(e)
            print(f"Attempt {attempt + 1}/{max_retries} failed: {error_msg[:100]}", file=sys.stderr)
            
            # Check for bot verification error
            if "Sign in to confirm you're not a bot" in error_msg or "bot" in error_msg.lower():
                print("\n⚠️  YouTube bot verification triggered", file=sys.stderr)
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 30  # 30s, 60s, 120s exponential backoff
                    print(f"Waiting {wait_time} seconds before retry...", file=sys.stderr)
                    time.sleep(wait_time)
                    continue
            
            # Check for rate limiting
            elif "HTTP Error 429" in error_msg or "Too Many Requests" in error_msg:
                print("\n⚠️  YouTube rate limiting (429)", file=sys.stderr)
                if attempt < max_retries - 1:
                    wait_time = (2 ** (attempt + 2)) * 30  # Longer wait for 429
                    print(f"Waiting {wait_time} seconds before retry...", file=sys.stderr)
                    time.sleep(wait_time)
                    continue
            
            # On last attempt, provide helpful hints
            if attempt == max_retries - 1:
                print(f"\n✗ Final error: {error_msg}", file=sys.stderr)
                
                if "Sign in to confirm" in error_msg:
                    print("\n💡 YouTube requires authentication. Try these solutions:", file=sys.stderr)
                    print("  1. Try a different video URL", file=sys.stderr)
                    print("  2. Wait 30+ minutes and try again", file=sys.stderr)
                    print("  3. Use a video from a smaller channel (less bot detection)", file=sys.stderr)
                    print("  4. Your ISP may be flagged - try via mobile hotspot", file=sys.stderr)
                elif "HTTP Error 429" in error_msg:
                    print("\n💡 YouTube is rate limiting. Wait 1+ hour before trying again.", file=sys.stderr)
                elif "unavailable" in error_msg.lower():
                    print("\n💡 The video might be private, deleted, or region-restricted", file=sys.stderr)
                elif "unable to download" in error_msg.lower():
                    print("\n💡 The video exists but cannot be downloaded (DRM or restrictions)", file=sys.stderr)
            
            return None
    
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
