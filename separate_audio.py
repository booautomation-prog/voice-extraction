#!/usr/bin/env python3
"""
Audio Source Separation
Separates audio into vocals, drums, bass, and other instruments using Demucs.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["PYTHONWARNINGS"] = "ignore"
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"


def configure_output_encoding():
    """Keep Windows consoles and subprocess pipes from crashing on Unicode."""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def add_packaged_ffmpeg_to_path():
    """Expose imageio-ffmpeg's binary when system FFmpeg is absent."""
    try:
        import imageio_ffmpeg

        ffmpeg_dir = str(Path(imageio_ffmpeg.get_ffmpeg_exe()).parent)
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
    except Exception:
        pass


def optional_env_int(name, default=None):
    value = os.environ.get(name)
    if value in (None, ""):
        return default
    return int(value)


def optional_env_float(name, default=None):
    value = os.environ.get(name)
    if value in (None, ""):
        return default
    return float(value)


def demucs_model_repo():
    repo = os.environ.get("DEMUCS_MODEL_REPO")
    if not repo:
        return None

    repo_path = Path(repo)
    if repo_path.is_dir():
        return repo_path

    return None


configure_output_encoding()
add_packaged_ffmpeg_to_path()


def separate_audio(audio_path, output_dir="separated", model="htdemucs"):
    """
    Separate audio into vocals, drums, bass, and other instruments.

    Args:
        audio_path: Path to audio file.
        output_dir: Directory to save separated audio.
        model: Demucs model to use.

    Returns:
        True if successful, False otherwise.
    """
    audio_path = Path(audio_path)

    if not audio_path.exists():
        print(f"Error: File '{audio_path}' not found", file=sys.stderr)
        return False

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        print(f"Separating audio: {audio_path.name}")
        print(f"Model: {model}")
        print(f"Output directory: {output_dir}\n")

        cmd = [
            sys.executable,
            "-m", "demucs.separate",
            "-n", model,
            "-o", str(output_path),
        ]

        repo_path = demucs_model_repo()
        if repo_path:
            cmd.extend(["--repo", str(repo_path)])

        shifts = optional_env_int("DEMUCS_SHIFTS", 0)
        segment = optional_env_int("DEMUCS_SEGMENT", 20)
        overlap = optional_env_float("DEMUCS_OVERLAP", 0.1)
        jobs = optional_env_int("DEMUCS_JOBS", 0)

        if shifts is not None:
            cmd.extend(["--shifts", str(shifts)])
        if segment is not None:
            cmd.extend(["--segment", str(segment)])
        if overlap is not None:
            cmd.extend(["--overlap", str(overlap)])
        if jobs is not None:
            cmd.extend(["--jobs", str(jobs)])

        cmd.append(str(audio_path))

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=os.environ.copy(),
        )

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        if result.returncode == 0:
            print("\nAudio separation completed successfully.")
            print_stem_info(output_path, audio_path.stem)
            return True

        if result.returncode < 0:
            print(
                f"\nDemucs was stopped by signal {-result.returncode}. "
                "On cloud hosting this usually means the job exceeded memory limits.",
                file=sys.stderr,
            )
        else:
            print(f"\nDemucs exited with code {result.returncode}", file=sys.stderr)
        return False

    except FileNotFoundError:
        print("Error: Demucs is not installed. Install with: pip install demucs", file=sys.stderr)
        return False
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        return False


def print_stem_info(output_dir, audio_stem):
    """Print information about separated stems."""
    output_dir = Path(output_dir)

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
            print(f"  - {stem_file.name} ({size_mb:.2f} MB)")


def list_models():
    """List available Demucs models."""
    return {
        "0d19c1c6": "Cloud default - single MDX model, lower memory",
        "htdemucs": "Recommended - best quality, higher complexity",
        "mdx": "Faster, good quality",
        "mdx_extra": "Highest quality, slowest",
        "htdemucs_ft": "Fine-tuned on various datasets",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Separate audio into vocals, drums, bass, and other instruments"
    )
    parser.add_argument("audio_file", nargs="?", help="Audio file to separate")
    parser.add_argument(
        "-o",
        "--output",
        default="separated",
        help="Output directory (default: separated)",
    )
    parser.add_argument(
        "-m",
        "--model",
        default="htdemucs",
        help="Model name or signature to use (default: htdemucs)",
    )
    parser.add_argument("--list-models", action="store_true", help="List models and exit")

    args = parser.parse_args()

    if args.list_models:
        print("Available Demucs models:\n")
        for model, description in list_models().items():
            print(f"  {model:20} - {description}")
        return 0

    if not args.audio_file:
        parser.error("audio_file is required unless --list-models is used")

    if not os.path.exists(args.audio_file):
        print(f"Error: Audio file '{args.audio_file}' not found", file=sys.stderr)
        return 1

    success = separate_audio(args.audio_file, args.output, args.model)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
