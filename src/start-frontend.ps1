# Start the Next.js frontend
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

Write-Host "Starting frontend server..." -ForegroundColor Cyan
Set-Location (Join-Path $scriptDir "ui")

# Open browser after delay (give Next.js time to start)
Start-Job -ScriptBlock {
    Start-Sleep -Seconds 4
    Start-Process "http://localhost:3000"
} | Out-Null

npm run dev:next
