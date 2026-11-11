@echo off
chcp 65001 >nul
title AI Studio Pro v14 - Multigenero & Clipping
cd /d "%~dp0"
echo ========================================================
echo   Iniciando AI Studio Pro v14 (Multigenero y Clipping)
echo ========================================================
"C:\Users\valle\AppData\Local\Python\pythoncore-3.14-64\python.exe" "aplicacion mejorada con gilab.py"
if errorlevel 1 (
    echo.
    echo [ERROR] Hubo un problema al cerrar o iniciar la aplicacion.
    pause
)
