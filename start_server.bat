@echo off
setlocal EnableExtensions
title MT5 Monitor - Server
cd /d "%~dp0"

set "PYTHON_EXE=.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo.
    echo  Python environment not found. Running installer first...
    call install.bat --no-pause
    if errorlevel 1 (
        echo.
        echo  [ERROR] Installation failed. Server cannot start.
        pause
        exit /b 1
    )
)

"%PYTHON_EXE%" -c "import uvicorn" >nul 2>&1
if errorlevel 1 (
    echo.
    echo  Core packages are missing. Running installer first...
    call install.bat --no-pause
    if errorlevel 1 (
        echo.
        echo  [ERROR] Installation failed. Server cannot start.
        pause
        exit /b 1
    )
)

:: Get local IPv4 address
powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.*' } | Sort-Object PrefixLength | Select-Object -First 1).IPAddress | Out-File -Encoding ascii '%TEMP%\mt5monitor_ip.txt'" 2>nul
set /p LOCAL_IP=<%TEMP%\mt5monitor_ip.txt
del %TEMP%\mt5monitor_ip.txt 2>nul
if "%LOCAL_IP%"=="" set LOCAL_IP=localhost

echo.
echo  ============================================
echo   MT5 Monitor -- starting server...
echo  ============================================
echo.
echo  Open in browser:
echo.
echo      This computer:      http://localhost:8000
echo      Other device (LAN): http://%LOCAL_IP%:8000
echo.
echo  To stop the server: close this window or Ctrl+C
echo  ============================================
echo.
"%PYTHON_EXE%" -m uvicorn main:app --host 0.0.0.0 --port 8000 --app-dir "%~dp0mt5_server"
pause
