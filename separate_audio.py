#!/usr/bin/env python3
"""
Audio Source Separation
Separates audio into vocals, drums, bass, and other instruments using Demucs
"""

import os
import sys
from pathlib import Path
import subprocess
import json

# Suppress Hugging Face warnings
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore'

# Set cache directory
cache_dir = Path.home() / '.cache' / 'demucs'
cache_dir.mkdir(parents=True, exist_ok=True)


def separate_audio(audio_path, output_dir="separated", model="htdemucs"):
    """
    Separate audio into vocals, drums, bass, and other instruments
    
    Args:
        audio_path (str): Path to audio file
        output_dir (str): Directory to save separated audio
        model (str): Model to use (htdemucs, mdx, or mdx_extra)
    
    Returns:
        bool: True if successful, False otherwise
    """
    audio_path = Path(audio_path)
    
    if not audio_path.exists():
        print(f"✗ Error: File '{audio_path}' not found", file=sys.stderr)
        return False
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        print(f"Separating audio: {audio_path.name}")
        print(f"Model: {model}")
        print(f"Output directory: {output_dir}\n")
        
        # Run demucs
        cmd = [
            "demucs",
            "-n", model,  # Model name
            "-o", str(output_path),
            str(audio_path)
        ]
        
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n✓ Audio separation completed successfully!")
            print_stem_info(output_path, audio_path.stem)
            return True
        else:
            print(f"\n✗ Error during separation", file=sys.stderr)
            return False
            
    except FileNotFoundError:
        print("✗ Error: Demucs is not installed. Install with: pip install demucs", file=sys.stderr)
        return False
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return False


def print_stem_info(output_dir, audio_stem):
    """Print information about separated stems"""
    output_dir = Path(output_dir)
    
    # Find the stems directory
    stems_dir = None
    for model_dir in output_dir.iterdir():
        if model_dir.is_dir():
            audio_dir = model_dir / audio_stem
            if audio_dir.exists():
                stems_dir = audio_dir
                break
    
    if stems_dir:
        print(f"\nSeparated stems saved in: {stems_dir}")
        print("\nGenerated files:")
        for stem_file in sorted(stems_dir.glob("*.wav")):
            stem_name = stem_file.stem
            size_mb = stem_file.stat().st_size / (1024 * 1024)
            print(f"  • {stem_file.name} ({size_mb:.2f} MB)")


def list_models():
    """List available Demucs models"""
    models = {
        "htdemucs": "Recommended - Best quality, higher complexity",
        "mdx": "Faster, good quality",
        "mdx_extra": "Highest quality, slowest",
        "htdemucs_ft": "Fine-tuned on various datasets",
    }
    return models


def main():
    parser = argparse.ArgumentParser(
        description='Separate audio into vocals, drums, bass, and other instruments'
    )
    parser.add_argument(
        'audio_file',
        help='Audio file to separate'
    )
    parser.add_argument(
        '-o', '--output',
        default='separated',
        help='Output directory (default: separated)'
    )
    parser.add_argument(
        '-m', '--model',
        default='htdemucs',
        choices=['htdemucs', 'mdx', 'mdx_extra', 'htdemucs_ft'],
        help='Model to use (default: htdemucs)'
    )
    parser.add_argument(
        '--list-models',
        action='store_true',
        help='List available models and exit'
    )
    
    args = parser.parse_args()
    
    if args.list_models:
        print("Available Demucs models:\n")
        for model, description in list_models().items():
            print(f"  {model:20} - {description}")
        return 0
    
    if not os.path.exists(args.audio_file):
        print(f"✗ Error: Audio file '{args.audio_file}' not found", file=sys.stderr)
        return 1
    
    success = separate_audio(args.audio_file, args.output, args.model)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
