@echo off
title MT5 Monitor — Serwer
cd /d "%~dp0"

:: Pobierz lokalny adres IP (Wi-Fi lub Ethernet)
for /f "tokens=2 delims=:" %%A in ('powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.PrefixOrigin -eq 'Dhcp' -or $_.PrefixOrigin -eq 'Manual' } | Sort-Object PrefixLength | Select-Object -First 1).IPAddress"') do set LOCAL_IP=%%A
set LOCAL_IP=%LOCAL_IP: =%
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
