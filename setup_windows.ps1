param(
    [string]$PythonExe = "",
    [switch]$UseTrustedHosts
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

function Resolve-Python {
    if ($PythonExe) {
        return @{ File = $PythonExe; Args = @() }
    }

    $PortablePython = Join-Path $ProjectRoot "portable-python\python.exe"
    if (Test-Path -LiteralPath $PortablePython) {
        return @{ File = $PortablePython; Args = @() }
    }

    $PyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($PyLauncher) {
        return @{ File = $PyLauncher.Source; Args = @("-3") }
    }

    $SystemPython = Get-Command python -ErrorAction SilentlyContinue
    if ($SystemPython) {
        return @{ File = $SystemPython.Source; Args = @() }
    }

    throw "Python was not found. Install Python 3.10+ or put portable Python at .\portable-python\python.exe."
}

function Invoke-Checked {
    param(
        [string]$File,
        [string[]]$Arguments
    )

    & $File @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $File $($Arguments -join ' ')"
    }
}

$Python = Resolve-Python
$VenvDir = Join-Path $ProjectRoot ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

Write-Host "Using Python: $($Python.File) $($Python.Args -join ' ')"

if (-not (Test-Path -LiteralPath $VenvPython)) {
    Write-Host "Creating local virtual environment in .venv..."
    Invoke-Checked $Python.File ($Python.Args + @("-m", "venv", $VenvDir))
}

Write-Host "Upgrading pip..."
try {
    Invoke-Checked $VenvPython @("-m", "pip", "install", "--upgrade", "pip")
}
catch {
    Write-Warning "Normal pip upgrade failed. Retrying with trusted PyPI hosts..."
    Invoke-Checked $VenvPython @(
        "-m", "pip", "install", "--upgrade", "pip",
        "--trusted-host", "pypi.org",
        "--trusted-host", "files.pythonhosted.org"
    )
}

Write-Host "Installing project dependencies..."
$InstallArgs = @("-m", "pip", "install", "-r", "requirements.txt")
if ($UseTrustedHosts) {
    $InstallArgs += @("--trusted-host", "pypi.org", "--trusted-host", "files.pythonhosted.org")
}

try {
    Invoke-Checked $VenvPython $InstallArgs
}
catch {
    if ($UseTrustedHosts) {
        throw
    }

    Write-Warning "Normal dependency install failed. Retrying with trusted PyPI hosts..."
    Invoke-Checked $VenvPython @(
        "-m", "pip", "install", "-r", "requirements.txt",
        "--trusted-host", "pypi.org",
        "--trusted-host", "files.pythonhosted.org"
    )
}

Write-Host ""
Write-Host "Setup complete."
Write-Host "Run the app with: .\run_windows.ps1"
