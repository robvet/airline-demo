# Start the Python backend server
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPath = Join-Path $scriptDir "../.venv/Scripts/Activate.ps1"

# Check if virtual environment is activated, if not activate it
if (-not $env:VIRTUAL_ENV) {
    if (Test-Path $venvPath) {
        Write-Host "Activating virtual environment..." -ForegroundColor Green
        & $venvPath
    } else {
        Write-Host "Virtual environment not found at $venvPath" -ForegroundColor Red
        Write-Host "Please create a virtual environment first: python -m venv .venv" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "Starting backend server..." -ForegroundColor Cyan
Set-Location $scriptDir
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000




