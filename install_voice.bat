@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo JARVIS virtual environment is missing.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m pip install SpeechRecognition PyAudioWPatch
if errorlevel 1 (
  echo.
  echo Voice installation failed. See the terminal output above.
  pause
  exit /b 1
)
echo.
echo Voice components installed. Start JARVIS and click PUSH TO TALK.
pause
