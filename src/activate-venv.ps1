# Activate the Python virtual environment
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPath = Join-Path $scriptDir "../.venv/Scripts/Activate.ps1"

if (Test-Path $venvPath) {
    Write-Host "Activating virtual environment..." -ForegroundColor Green
    & $venvPath
} else {
    Write-Host "Virtual environment not found at $venvPath" -ForegroundColor Red
    Write-Host "Please create a virtual environment first: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}
