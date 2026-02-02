# Start both frontend and backend
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPath = Join-Path $scriptDir "../.venv/Scripts/Activate.ps1"

# Check if virtual environment exists
if (-not (Test-Path $venvPath)) {
    Write-Host "Virtual environment not found at $venvPath" -ForegroundColor Red
    Write-Host "Please create a virtual environment first: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

Write-Host "Starting Pacific Airlines Demo..." -ForegroundColor Cyan
Write-Host ""

# Start backend in a new terminal window
Write-Host "Starting backend (main.py)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptDir'; & '$venvPath'; python main.py"

# Give backend a moment to initialize
Start-Sleep -Seconds 2

# Start frontend in a new terminal window
Write-Host "Starting frontend (Streamlit)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptDir\ui'; & '$venvPath'; streamlit run streamlit_app.py"

# Open browser after delay
Start-Job -ScriptBlock {
    Start-Sleep -Seconds 4
    Start-Process "http://localhost:8501"
} | Out-Null

Write-Host ""
Write-Host "Both servers starting in separate windows..." -ForegroundColor Cyan
Write-Host "  Backend:  Terminal REPL (main.py)" -ForegroundColor Yellow
Write-Host "  Frontend: http://localhost:8501" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to exit this launcher..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
