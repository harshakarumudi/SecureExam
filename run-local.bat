@echo off
title SecureExam - Local Windows Runner
echo ========================================================
echo   SecureExam - Starting Locally (No Docker Required)
echo ========================================================
echo.
cd /d "%~dp0"

echo [1/3] Initializing local database...
call .\venv\Scripts\python.exe -c "import asyncio; from backend.app.db.init_db import init_db; asyncio.run(init_db())"

echo [2/3] Starting FastAPI Backend on http://localhost:8000 ...
start "SecureExam Backend" cmd /k "cd /d %~dp0 && call .\venv\Scripts\activate.bat && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

echo [3/3] Starting Vite Frontend on http://localhost:3000 ...
start "SecureExam Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev"

echo.
echo ========================================================
echo  [SUCCESS] SecureExam servers are starting!
echo ========================================================
echo  - Frontend Web Portal : http://localhost:3000
echo  - Backend API Docs    : http://localhost:8000/docs
echo ========================================================
echo.
timeout /t 3 >nul
start http://localhost:3000
