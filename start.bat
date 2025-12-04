@echo off
title IP Logger
color 9
cls

echo Checking for port conflicts...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
    echo Killing process using port 5000 (PID: %%a)
    taskkill /F /PID %%a >nul 2>&1
)

echo Checking for cloudflared processes...
taskkill /F /IM cloudflared.exe >nul 2>&1

echo Installing dependencies...
pip install -r requirements.txt >nul 2>&1
cls
echo Starting IP Logger...
python main.py
pause
