@echo off
setlocal enabledelayedexpansion
title Industrial Electrical SLD RCA - 1-Click Launcher
echo =====================================================================
echo    [1-CLICK LAUNCHER] Industrial Electrical SLD Multi-Agent RCA
echo =====================================================================
echo.

cd /d "%~dp0"

:: 1. Check Python environment
set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    echo [!] Virtual environment not found in .venv. Falling back to system python...
    set "PYTHON_EXE=python"
)

:: 2. Launch FastAPI Backend on Port 8001 in a new window
echo [*] Launching Multi-Agent FastAPI Backend on http://localhost:8001 ...
start "Electrical RCA - Backend API (:8001)" cmd /k "cd /d "%~dp0" && "%PYTHON_EXE%" -m uvicorn agents.electrical_app:app --host 0.0.0.0 --port 8001 --reload"

:: 3. Launch Next.js Frontend on Port 3000 in a new window
echo [*] Launching Next.js Interactive Dashboard on http://localhost:3000 ...
start "Electrical RCA - Web UI (:3000)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

:: 4. Wait for servers to spin up
echo [*] Waiting 3 seconds for services to initialize...
timeout /t 3 /nobreak >nul

:: 5. Open browser automatically
echo [*] Opening Industrial Electrical RCA Dashboard in browser...
start http://localhost:3000

echo.
echo =====================================================================
echo    [SUCCESS] All 5 Agents and Interactive Canvas are Live!
echo    - Dashboard: http://localhost:3000
echo    - API Docs:  http://localhost:8001/docs
echo    (Close the individual server windows to stop)
echo =====================================================================
echo.
pause
