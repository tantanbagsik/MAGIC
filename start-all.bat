@echo off
chcp 65001 >nul
title VoiceAI - All Services

REM Check/Start Redis
echo [1/5] Starting Redis...
"C:\Program Files\Redis\redis-cli.exe" ping >nul 2>&1
if %errorlevel% neq 0 (
    start "" "C:\Program Files\Redis\redis-server.exe"
    timeout /t 2 >nul
)
echo Redis: OK

REM Check MongoDB Atlas Connection
echo [2/5] Checking MongoDB Atlas...
python -c "from dotenv import load_dotenv; load_dotenv(); from config import config; print(config.MONGODB_URL[:50]+'...')" >nul 2>&1
if %errorlevel% neq 0 (
    echo MongoDB URL not configured!
    echo Please edit .env file with your MongoDB Atlas connection string
    pause
    exit /b 1
)
echo MongoDB Atlas: OK

REM Start Backend
echo [3/5] Starting Backend (FastAPI)...
start "VoiceAI Backend" cmd /k "cd /d %~dp0 && python main.py"

REM Start Frontend React
echo [4/5] Starting Frontend (React)...
start "VoiceAI React" cmd /k "cd /d %~dp0frontend-react && npm run dev"

REM Start Frontend Vue
echo [5/5] Starting Frontend (Vue)...
start "VoiceAI Vue" cmd /k "cd /d %~dp0frontend-vue && npm run dev"

echo.
echo ====================================
echo   All Services Started!
echo ====================================
echo.
echo Access URLs:
echo   - React:  http://localhost:3000
echo   - Vue:    http://localhost:3001
echo   - API:    http://localhost:8000
echo   - Docs:   http://localhost:8000/docs
echo.
echo Open your browser to test the app!
echo.
pause
