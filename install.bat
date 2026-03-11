@echo off
setlocal EnableDelayedExpansion
title MT5 Monitor — Instalacja
cd /d "%~dp0"

echo.
echo  ============================================================
echo   MT5 Monitor — Instalator
echo  ============================================================
echo.

:: ── 1. Sprawdź czy Python jest zainstalowany ─────────────────────────────────
echo  [1/4] Sprawdzanie Pythona...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [BLAD] Python nie jest zainstalowany lub nie jest w PATH!
    echo.
    echo  Pobierz Python 3.11 lub nowszy ze strony:
    echo      https://www.python.org/downloads/
    echo.
    echo  WAZNE: podczas instalacji zaznacz opcje
    echo      "Add Python to PATH"
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo  Znaleziono: %%v

:: ── 2. Utwórz środowisko wirtualne ──────────────────────────────────────────
echo.
echo  [2/4] Tworzenie srodowiska wirtualnego (.venv)...
if exist ".venv\Scripts\python.exe" (
    echo  Srodowisko juz istnieje — pomijam tworzenie.
) else (
    python -m venv .venv
    if errorlevel 1 (
        echo  [BLAD] Nie udalo sie utworzyc srodowiska wirtualnego!
        pause
        exit /b 1
    )
    echo  Srodowisko utworzone.
)

:: ── 3. Zainstaluj pakiety ─────────────────────────────────────────────────────
echo.
echo  [3/4] Instalowanie pakietow Python (MT5 + FastAPI)...
echo  (to moze chwile potrwac)
echo.
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
set "REQ_FILE=mt5_server\requirements.txt"
set "MISSING_REQ=%TEMP%\mt5monitor_missing_requirements.txt"
set "CORE_REQ=%TEMP%\mt5monitor_core_requirements.txt"
set "MISSING_CORE=%TEMP%\mt5monitor_missing_core_requirements.txt"

.venv\Scripts\python.exe mt5_server\scripts\filter_missing_requirements.py "%REQ_FILE%" "%MISSING_REQ%"
if errorlevel 1 (
    echo  [BLAD] Nie udalo sie przeskanowac requirements!
    pause
    exit /b 1
)

for %%I in ("%MISSING_REQ%") do set "MISSING_SIZE=%%~zI"
if "!MISSING_SIZE!"=="0" (
    echo  Wszystkie wymagane pakiety sa juz zainstalowane.
) else (
    .venv\Scripts\python.exe -m pip install -r "%MISSING_REQ%" --ignore-requires-python 2>nul
    if errorlevel 1 (
        echo.
        echo  Probuje instalacje tylko podstawowych pakietow (bez cTrader)...
        (
            echo MetaTrader5
            echo fastapi
            echo uvicorn[standard]
            echo pydantic-settings
            echo pandas
            echo python-dotenv
            echo slowapi
            echo requests==2.32.3
        ) > "%CORE_REQ%"

        .venv\Scripts\python.exe mt5_server\scripts\filter_missing_requirements.py "%CORE_REQ%" "%MISSING_CORE%"
        if errorlevel 1 (
            echo  [BLAD] Nie udalo sie przeskanowac podstawowych pakietow!
            del "%MISSING_REQ%" 2>nul
            del "%CORE_REQ%" 2>nul
            del "%MISSING_CORE%" 2>nul
            pause
            exit /b 1
        )

        for %%I in ("%MISSING_CORE%") do set "MISSING_CORE_SIZE=%%~zI"
        if "!MISSING_CORE_SIZE!"=="0" (
            echo  Podstawowe pakiety sa juz zainstalowane.
        ) else (
            .venv\Scripts\python.exe -m pip install -r "%MISSING_CORE%"
            if errorlevel 1 (
                echo  [BLAD] Instalacja podstawowych pakietow nie powiodla sie!
                del "%MISSING_REQ%" 2>nul
                del "%CORE_REQ%" 2>nul
                del "%MISSING_CORE%" 2>nul
                pause
                exit /b 1
            )
        )

        echo.
        echo  [UWAGA] Nie udalo sie zainstalowac pelnego stosu cTrader.
        echo  Obsluga kont cTrader bedzie niedostepna.
        echo  Upewnij sie ze masz Python 3.11 lub nowszy i uruchom ponownie install.bat
    )
)

del "%MISSING_REQ%" 2>nul
del "%CORE_REQ%" 2>nul
del "%MISSING_CORE%" 2>nul

:: ── 4. Utwórz plik .env jeśli nie istnieje ───────────────────────────────────
echo.
echo  [4/4] Sprawdzanie konfiguracji...
if not exist "mt5_server\.env" (
    echo  Tworzenie przykladowego pliku konfiguracyjnego mt5_server\.env ...
    (
        echo # Klucz API do autoryzacji — zmien na wlasny losowy ciag znakow
        echo API_KEY=zmien_mnie_na_losowy_klucz
    ) > mt5_server\.env
    echo.
    echo  [UWAGA] Utworzono plik mt5_server\.env z domyslnymi wartosciami.
    echo  Otworz ten plik i ustaw wlasny API_KEY przed uruchomieniem serwera!
) else (
    echo  Plik mt5_server\.env juz istnieje — pomijam.
)

:: ── Zaktualizuj start_server.bat do ścieżek względnych ────────────────────────
echo.
echo  ============================================================
echo   Instalacja zakonczona pomyslnie!
echo  ============================================================
echo.
echo  Co dalej:
echo.
echo  1. Upewnij sie ze terminal MetaTrader 5 jest uruchomiony
echo     na tym samym komputerze.
echo.
echo  2. Uruchom serwer klikajac dwa razy w:
echo         start_server.bat
echo.
echo  3. Otworz przegladarke i wpisz w pasek adresu:
echo         http://localhost:8000
echo.
echo  4. Zaloguj sie podajac dane konta MT5 (login, haslo, serwer).
echo.
echo  ============================================================
echo.
pause
