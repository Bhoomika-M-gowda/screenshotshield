
@echo off
title ScreenshotShield Launcher

cd /d "%~dp0"

echo Starting ScreenshotShield Backend...

start "ScreenshotShield Backend" cmd /k "cd /d ""%~dp0backend"" && python -m uvicorn main:app --port 8000"

echo Starting ScreenshotShield Frontend...

start "ScreenshotShield Frontend" cmd /k "cd /d ""%~dp0frontend"" && npm run dev -- --host 127.0.0.1"

echo Waiting for frontend to start...

:WAIT
timeout /t 2 /nobreak >nul
curl -s http://127.0.0.1:5173/ >nul

if errorlevel 1 goto WAIT

echo Opening ScreenshotShield in Chrome...

start "" chrome.exe "http://127.0.0.1:5173/"

exit
