@echo off
title MT5 Monitor — Serwer
cd /d "%~dp0"
echo.
echo  ============================================
echo   MT5 Monitor — uruchamianie serwera...
echo  ============================================
echo.
echo  Po uruchomieniu otwórz przegladarke i wpisz:
echo.
echo      http://localhost:8000
echo.
echo  (NIE szukaj w Google — wpisz w pasek adresu!)
echo.
echo  Aby zatrzymac serwer: zamknij to okno lub Ctrl+C
echo  ============================================
echo.
.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload --app-dir "%~dp0mt5_server"
pause
