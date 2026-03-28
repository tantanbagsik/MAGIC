@echo off
chcp 65001 >nul
title VoiceAI MongoDB Setup

echo ====================================
echo   VoiceAI - MongoDB Setup
echo ====================================
echo.
echo Please enter your MongoDB Atlas password
echo (from MongoDB Atlas > Security > Database Access)
echo.

set /p PASSWORD="MongoDB Password: "

echo MONGODB_URL=mongodb+srv://Vercel-Admin-atlas-aero-river:%PASSWORD%@atlas-aero-river.dyp83ag.mongodb.net/?appName=atlas-aero-river > .env
echo DATABASE_NAME=voice_ai_support >> .env
echo OLLAMA_BASE_URL=http://localhost:11434 >> .env
echo OLLAMA_MODEL=llama3.2 >> .env

echo.
echo .env file created successfully!
echo.
echo Starting VoiceAI services...
timeout /t 2 >nul
