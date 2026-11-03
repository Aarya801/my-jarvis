@echo off
setlocal
cd /d "%~dp0"
if not exist logs mkdir logs

REM Self-heal on first launch after Python is installed or replaced.
if not exist .venv\Scripts\python.exe (
  echo [JARVIS] Creating the local Python environment...
  python -m venv .venv >> logs\launch.log 2>&1
)

if not exist .venv\Scripts\python.exe (
  echo [JARVIS] Could not create the environment. See logs\launch.log
  pause
  exit /b 1
)

REM Install UI, web, and push-to-talk dependencies only when absent.
.venv\Scripts\python.exe -c "import PySide6, requests, speech_recognition, pyttsx3" >nul 2>&1
if errorlevel 1 (
  echo [JARVIS] Installing or repairing JARVIS components. This may take a minute...
  .venv\Scripts\python.exe -m pip install -r requirements.txt >> logs\launch.log 2>&1
)

.venv\Scripts\python.exe main.py >> logs\launch.log 2>&1
if errorlevel 1 (
  echo [JARVIS] Stopped unexpectedly. Details: logs\launch.log
  pause
)
