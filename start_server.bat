@echo off
title MT5 Monitor — Serwer
cd /d "%~dp0"

:: Sprawdz czy .venv istnieje
if not exist ".venv\Scripts\python.exe" (
    echo.
    echo  BLAD: Nie znaleziono srodowiska Python!
    echo  Uruchom najpierw plik install.bat, a dopiero potem start_server.bat
    echo.
    pause
    exit /b 1
)

:: Pobierz lokalny adres IP
powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.*' } | Sort-Object PrefixLength | Select-Object -First 1).IPAddress | Out-File -Encoding ascii '%TEMP%\mt5monitor_ip.txt'" 2>nul
set /p LOCAL_IP=<%TEMP%\mt5monitor_ip.txt
del %TEMP%\mt5monitor_ip.txt 2>nul
if "%LOCAL_IP%"=="" set LOCAL_IP=localhost

echo.
echo  ============================================
echo   MT5 Monitor -- uruchamianie serwera...
echo  ============================================
echo.
echo  Po uruchomieniu otwórz przegladarke i wpisz:
echo.
echo      Na tym komputerze:   http://localhost:8000
echo      Z innego urzadzenia: http://%LOCAL_IP%:8000
echo.
echo  (NIE szukaj w Google -- wpisz w pasek adresu!)
echo.
echo  Aby zatrzymac serwer: zamknij to okno lub Ctrl+C
echo  ============================================
echo.
.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload --app-dir "%~dp0mt5_server"
pause
