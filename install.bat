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
.venv\Scripts\python.exe -m pip install -r mt5_server\requirements.txt --ignore-requires-python 2>nul
if errorlevel 1 (
    echo.
    echo  Probuje instalacje bez ctrader-open-api (wymaga kompilatora C++)...
    .venv\Scripts\python.exe -m pip install MetaTrader5 fastapi "uvicorn[standard]" pydantic-settings pandas python-dotenv slowapi requests
    if errorlevel 1 (
        echo  [BLAD] Instalacja podstawowych pakietow nie powiodla sie!
        pause
        exit /b 1
    )
    echo.
    echo  [UWAGA] ctrader-open-api nie zostal zainstalowany.
    echo  Obsluga kont cTrader bedzie niedostepna.
    echo  Aby ja wlaczyc, zainstaluj Microsoft C++ Build Tools:
    echo  https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo  a nastepnie uruchom: .venv\Scripts\python.exe -m pip install ctrader-open-api
)

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
