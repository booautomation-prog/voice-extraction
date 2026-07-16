param(
    [int]$Port = 5000
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $VenvPython)) {
    throw "Local Python environment was not found. Run .\setup_windows.ps1 first."
}

$env:PORT = "$Port"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

Write-Host "Voice Extraction Studio"
Write-Host "Open: http://127.0.0.1:$Port"
Write-Host "Press Ctrl+C in this window to stop the server."
Write-Host ""

& $VenvPython app.py
