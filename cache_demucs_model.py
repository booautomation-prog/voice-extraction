#!/usr/bin/env python3
"""Download Demucs legacy model files into a local model repository."""

import shutil
import sys
import urllib.request
from pathlib import Path

import yaml
from demucs.pretrained import REMOTE_ROOT, _parse_remote_files
from demucs.repo import check_checksum


def signatures_for_model(model_name):
    bag_file = REMOTE_ROOT / f"{model_name}.yaml"
    if not bag_file.exists():
        return [model_name], None

    with open(bag_file, encoding="utf-8") as file:
        bag = yaml.safe_load(file)

    return bag["models"], bag_file


def download_file(url, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {target.name}")
    with urllib.request.urlopen(url, timeout=120) as response:
        with open(target, "wb") as file:
            shutil.copyfileobj(response, file)


def main():
    model_name = sys.argv[1] if len(sys.argv) > 1 else "mdx"
    repo_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "model_repo")
    repo_dir.mkdir(parents=True, exist_ok=True)

    remote_models = _parse_remote_files(REMOTE_ROOT / "files.txt")
    signatures, bag_file = signatures_for_model(model_name)

    if bag_file:
        shutil.copy2(bag_file, repo_dir / bag_file.name)
        print(f"Copied bag definition: {bag_file.name}")

    for signature in signatures:
        url = remote_models.get(signature)
        if not url:
            raise SystemExit(f"No legacy Demucs URL found for model signature: {signature}")

        filename = url.rsplit("/", 1)[-1]
        target = repo_dir / filename
        checksum = Path(filename).stem.rsplit("-", 1)[-1] if "-" in Path(filename).stem else None

        if target.exists():
            print(f"Using cached {target.name}")
        else:
            download_file(url, target)

        if checksum:
            check_checksum(target, checksum)
            print(f"Verified {target.name}")

    print(f"Demucs model '{model_name}' is cached in {repo_dir.resolve()}")


if __name__ == "__main__":
    main()
