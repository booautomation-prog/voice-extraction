# Portable Windows Setup

Use this when you want to copy Voice Extraction Studio to another Windows computer.

## Recommended Way

Copy this project folder to the other computer, then run setup there.

Do not copy these generated folders unless you specifically want the old outputs:

- `.venv`
- `__pycache__`
- `downloads`
- `uploads`
- `separated`
- `cache`
- `model_cache`

On the new computer:

```powershell
cd "path\to\voice extraction"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup_windows.ps1
.\run_windows.ps1
```

Then open:

```text
http://127.0.0.1:5000
```

## Portable Python Option

If the computer should not use an installed Python, put a portable Python folder here:

```text
voice extraction\
  portable-python\
    python.exe
```

Then run:

```powershell
.\setup_windows.ps1
.\run_windows.ps1
```

Use a portable Python distribution that already supports `pip` and `venv`. WinPython is usually easier than the official Python embeddable zip, because the embeddable zip does not include a normal `pip`/`venv` workflow by default.

You can also point setup at a specific Python:

```powershell
.\setup_windows.ps1 -PythonExe "D:\Tools\Python311\python.exe"
```

## If Pip Has SSL Certificate Errors

Some Windows machines cannot verify Python HTTPS certificates correctly. If setup fails with `CERTIFICATE_VERIFY_FAILED`, run:

```powershell
.\setup_windows.ps1 -UseTrustedHosts
```

## What Is Included

The project uses `imageio-ffmpeg`, so the app does not need system FFmpeg installed.

The first full separation run may download Demucs model files. This can take time and several hundred MB. Internet is required for:

- Installing Python packages
- Downloading YouTube audio
- Downloading Demucs models on first run

## Fully Offline Copy

For a fully offline computer, prepare the project once on an internet-connected computer, then copy:

- The project source files
- `.venv`
- `model_cache`, if you configured model caching into the project

This can be several GB because `torch`, `demucs`, and model files are large. A safer normal workflow is to copy only the project source and run `.\setup_windows.ps1` on each computer.
