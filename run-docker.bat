@echo off
title SecureExam - Docker Runner
echo ========================================================
echo   SecureExam - Starting with Docker Compose
echo ========================================================
echo.
cd /d "%~dp0"

echo [1/2] Checking Docker Daemon...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ========================================================
    echo  [!] DOCKER DESKTOP IS NOT RUNNING!
    echo ========================================================
    echo  Please follow these 2 steps:
    echo  1. Open 'Docker Desktop' from your Windows Start Menu.
    echo  2. Wait until the whale icon appears in your taskbar.
    echo  3. Then double-click this file again or press any key.
    echo ========================================================
    echo.
    pause
    exit /b 1
)

echo [2/2] Starting containers (Frontend, Backend, Postgres)...
docker compose up -d

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo  [SUCCESS] All SecureExam containers are running!
    echo ========================================================
    echo  - Frontend Web Portal : http://localhost:3000
    echo  - Backend API Docs    : http://localhost:8000/docs
    echo ========================================================
    echo.
    timeout /t 2 >nul
    start http://localhost:3000
) else (
    echo.
    echo [ERROR] Failed to start Docker containers.
)

pause
