@echo off
title ClaimVision AI - FastAPI Backend Server
cd /d "%~dp0"
echo ===================================================================
echo  Starting ClaimVision AI Backend Service (Port 8000)
echo ===================================================================
python -m uvicorn api:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
pause
