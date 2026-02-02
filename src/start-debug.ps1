# Start frontend + backend (debug mode) + open browser
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Activate venv
$venvPath = Join-Path $scriptDir "../.venv/Scripts/Activate.ps1"
if (Test-Path $venvPath) { & $venvPath }

# Start frontend in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptDir\ui'; npm run dev:next"

# Start backend with debugger
Set-Location $scriptDir

# Open browser after delay
Start-Job -ScriptBlock {
    Start-Sleep -Seconds 4
    Start-Process "http://localhost:3000"
} | Out-Null

# Run backend with debugpy
python -m debugpy --listen 5678 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
