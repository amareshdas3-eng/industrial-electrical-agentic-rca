# =====================================================================
#   Industrial Electrical SLD Multi-Agent RCA - PowerShell 1-Click Launcher
# =====================================================================

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "   [1-CLICK LAUNCHER] Industrial Electrical SLD Multi-Agent RCA" -ForegroundColor Yellow
Write-Host "=====================================================================" -ForegroundColor Cyan

$WorkspaceRoot = $PSScriptRoot
$PythonExe = Join-Path $WorkspaceRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Host "[!] Virtual environment not found in .venv. Falling back to 'python'..." -ForegroundColor Yellow
    $PythonExe = "python"
}

# 1. Start FastAPI Backend (Port 8001) in separate process
Write-Host "[*] Launching Multi-Agent FastAPI Backend on http://localhost:8001..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$WorkspaceRoot'; & '$PythonExe' -m uvicorn agents.electrical_app:app --host 0.0.0.0 --port 8001 --reload"

# 2. Start Next.js Frontend (Port 3000) in separate process
Write-Host "[*] Launching Next.js Interactive Dashboard on http://localhost:3000..." -ForegroundColor Green
$FrontendDir = Join-Path $WorkspaceRoot "frontend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$FrontendDir'; npm run dev"

# 3. Wait and open browser
Write-Host "[*] Waiting 3 seconds for services to initialize..." -ForegroundColor DarkGray
Start-Sleep -Seconds 3

Write-Host "[*] Opening Dashboard in default browser..." -ForegroundColor Cyan
Start-Process "http://localhost:3000"

Write-Host "`n=====================================================================" -ForegroundColor Cyan
Write-Host "   [SUCCESS] Platform Running!" -ForegroundColor Green
Write-Host "   - Interactive Dashboard: http://localhost:3000"
Write-Host "   - FastAPI Swagger Docs:  http://localhost:8001/docs"
Write-Host "=====================================================================" -ForegroundColor Cyan
