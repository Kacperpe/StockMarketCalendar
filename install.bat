@echo off
setlocal EnableExtensions
title MT5 Monitor - Installation
cd /d "%~dp0"

set "NO_PAUSE=0"
if /I "%~1"=="--no-pause" set "NO_PAUSE=1"

set "PYTHON_EXE=.venv\Scripts\python.exe"
set "CORE_REQ=mt5_server\requirements.txt"
set "CTRADER_REQ=mt5_server\requirements-ctrader.txt"

echo.
echo  ============================================================
echo   MT5 Monitor - Installer
echo  ============================================================
echo.

echo  [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERROR] Python is not installed or not in PATH.
    echo  Install Python 3.11+ from:
    echo      https://www.python.org/downloads/
    echo  During installation, enable: "Add Python to PATH".
    call :finish 1
    goto :eof
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo  Found: %%v

echo.
echo  [2/4] Creating virtual environment (.venv)...
if exist "%PYTHON_EXE%" (
    echo  Virtual environment already exists - skipping.
) else (
    python -m venv .venv
    if errorlevel 1 (
        echo  [ERROR] Failed to create virtual environment.
        call :finish 1
        goto :eof
    )
    echo  Virtual environment created.
)

echo.
echo  [3/4] Installing core dependencies (MT5 mode)...
"%PYTHON_EXE%" -m pip install --upgrade pip
if errorlevel 1 (
    echo  [ERROR] Failed to update pip.
    call :finish 1
    goto :eof
)

"%PYTHON_EXE%" -m pip install -r "%CORE_REQ%"
if errorlevel 1 (
    echo.
    echo  [ERROR] Failed to install core dependencies.
    echo  Check internet / firewall and rerun install.bat.
    call :finish 1
    goto :eof
)

echo.
echo  [4/4] Installing optional cTrader dependencies...
"%PYTHON_EXE%" -m pip install -r "%CTRADER_REQ%"
if errorlevel 1 (
    echo.
    echo  [WARNING] Optional cTrader dependencies were not installed.
    echo  MT5 mode is ready and fully usable.
    echo  To retry cTrader later, run:
    echo      .venv\Scripts\python.exe -m pip install -r mt5_server\requirements-ctrader.txt
) else (
    echo  cTrader dependencies installed successfully.
)

echo.
echo  [Config] Checking mt5_server\.env...
if not exist "mt5_server\.env" (
    if exist "mt5_server\.env.example" (
        copy /Y "mt5_server\.env.example" "mt5_server\.env" >nul
        echo  Created mt5_server\.env from .env.example.
    ) else (
        (
            echo # API key for local auth
            echo API_KEY=change_me_to_a_random_value
        ) > "mt5_server\.env"
        echo  Created default mt5_server\.env.
    )
) else (
    echo  mt5_server\.env already exists - skipping.
)

echo.
echo  ============================================================
echo   Installation finished.
echo  ============================================================
echo  Start the app with: start_server.bat
call :finish 0
goto :eof

:finish
set "EXIT_CODE=%~1"
if "%NO_PAUSE%"=="0" pause
exit /b %EXIT_CODE%
