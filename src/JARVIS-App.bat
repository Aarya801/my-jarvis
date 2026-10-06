@echo off
setlocal
title J.A.R.V.I.S. Local Bridge
echo.
echo  J.A.R.V.I.S. - Local Windows Bridge
echo  ====================================
echo.
echo  Starting the loopback bridge on 127.0.0.1:8765...
echo  Keep this window open while PC-control features are needed.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0jarvis-bridge.ps1"
endlocal
