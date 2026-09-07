@echo off
title ClaimVision AI - Master Launcher
cd /d "%~dp0"
echo ===================================================================
echo  Launching ClaimVision AI: Backend + Next.js UI
echo ===================================================================

start "ClaimVision Backend" cmd /c "python -m uvicorn api:app --app-dir backend --host 127.0.0.1 --port 8000"
timeout /t 2 /nobreak >nul

start "ClaimVision UI" cmd /c "cd frontend && npm run dev"
timeout /t 3 /nobreak >nul

start http://localhost:3000
echo ===================================================================
echo  ClaimVision AI is live!
echo  Backend:  http://127.0.0.1:8000/docs
echo  Frontend: http://localhost:3000
echo ===================================================================
