# 📈 MT5 & cTrader Monitor

A real-time trading account dashboard for **MetaTrader 5** and **cTrader** accounts.  
Monitor your balance, open positions, performance statistics, and P&L calendar — all in one browser tab.

---

## ⬇️ Download

**Latest release (recommended):**  
[📦 Download from Releases](https://github.com/Kacperpe/StockMarketCalendar/releases/latest)

**Or download the latest code as ZIP directly:**  
[📦 Download StockMarketCalendar.zip](https://github.com/Kacperpe/StockMarketCalendar/archive/refs/heads/main.zip)

**Option — paste in PowerShell (Windows):**
```powershell
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/Kacperpe/StockMarketCalendar/archive/refs/heads/main.zip' -OutFile 'StockMarketCalendar.zip'; Expand-Archive 'StockMarketCalendar.zip' -DestinationPath 'C:\StockMarketCalendar'; Remove-Item 'StockMarketCalendar.zip'"
```

---

## 📋 Table of Contents / Spis treści

- [⬇️ Download](#️-download)

- 🇬🇧 **English**
  - [Features](#features)
  - [Requirements](#requirements)
  - [Getting cTrader Client ID & Secret](#getting-ctrader-client-id--secret) ← *read before installing if you use cTrader*
  - [Installation — step by step](#installation--step-by-step)
  - [Troubleshooting](#troubleshooting)
  - [Stopping the server](#stopping-the-server)
  - [Notes](#notes)

- 🇵🇱 **Polski**
  - [Funkcje](#funkcje)
  - [Wymagania](#wymagania)
  - [Jak uzyskać Client ID i Client Secret dla cTrader?](#jak-uzyska-client-id-i-client-secret-dla-ctrader) ← *przeczytaj przed instalacją gdy używasz cTrader*
  - [Instalacja — krok po kroku](#instalacja--krok-po-kroku)
  - [Rozwiązywanie problemów](#rozwizywanie-problemw)
  - [Zatrzymanie serwera](#zatrzymanie-serwera)
  - [Uwagi](#uwagi)

---

## 🇬🇧 English

### Features

| Feature | Description |
|---|---|
| 📊 **Live account overview** | Balance, equity, margin, floating P&L |
| 📋 **Open positions** | All open trades with entry price, current price, swap, P&L |
| 📈 **Full statistics** | Win rate, profit factor, Sharpe ratio, Z-Score, expectancy, drawdown and more |
| 📅 **Monthly P&L calendar** | Myfxbook-style calendar showing daily profit/loss |
| 📉 **Equity curve** | Full balance history chart since account opening |
| 🎨 **Themes** | Dark / Light (Myfxbook colours) / Custom |
| 👁️ **Panel visibility** | Show/hide each panel independently |
| 🔗 **MT5 support** | Connects to local MetaTrader 5 terminal (read-only investor password) |
| 🔗 **cTrader support** | Connects via Spotware OAuth2 (no terminal needed) |

---

### Requirements

- **Windows 10 / 11** (64-bit)
- **Python 3.11 or newer** — download from [python.org](https://www.python.org/downloads/)  
  ⚠️ During installation tick **"Add Python to PATH"**
- **MetaTrader 5 terminal** — running **and logged in** to your account *(only for MT5 accounts)*  
  ⚠️ Just having MT5 open is not enough — you must be logged in to a trading account
- Internet connection *(only for cTrader accounts)*
- For **cTrader support on Windows**: install **Microsoft C++ Build Tools** first, then run `install.bat`  
  https://visualstudio.microsoft.com/visual-cpp-build-tools/

---

### Getting cTrader Client ID & Secret

> ⚠️ **cTrader users: complete this section before installation.** You will need the Client ID and Client Secret in step 6.

1. Go to [connect.spotware.com](https://connect.spotware.com) and log in (same credentials as your cTrader platform)
2. Click **Applications** → **New Application**
3. Fill in any name (e.g. `MyMonitor`), and set the Redirect URI field exactly to:
   ```
   http://localhost:8000/auth/ctrader/callback
   ```
4. Save — you will see your **Client ID** and **Client Secret**. Copy them somewhere safe.

**Linking your cTrader trading account to the application:**

5. In the Spotware Connect panel, open your newly created application and click the **Accounts** tab
6. Click **Add Account** and enter your cTrader account number
   > 💡 Your cTrader account number is the numeric ID visible in the top-left corner of the cTrader desktop platform after logging in (e.g. `12345678`)
7. You can add multiple accounts — all will be selectable in the dashboard after authorization
   > 💡 Accounts are shown as **LIVE/DEMO** in the app. Select the correct one before connecting.

> 💡 If you skip steps 5–7, only accounts assigned by your broker will appear after login.

---

### Installation — step by step

> 💡 **cTrader users:** Before step 6, make sure you've completed [Getting cTrader Client ID & Secret](#getting-ctrader-client-id--secret) above.

1. **Download the project**  
   Go to the [project page on GitHub](https://github.com/Kacperpe/StockMarketCalendar), click the green **Code** → **Download ZIP** button, then extract the folder anywhere (e.g. `C:\MT5Monitor`).

2. **Run the installer**  
   Double-click `install.bat` (or just run `start_server.bat` and it will auto-run installer when needed).  
   It will:
   - Check that Python is installed
   - Prepare an isolated environment for the app (you don't need to know what this means)
   - Scan installed packages and install only missing or mismatched requirements
   - Install all required packages
   - Create a default `mt5_server\.env` config file

3. **Configure the app** *(optional)*  
   Open `mt5_server\.env` in Notepad and set your `API_KEY` to any random string you like.  
   The MT5 login/password/server can instead be entered directly in the browser.

4. **Start the server**  
   Double-click `start_server.bat`.  
   A console window will appear — leave it open while using the app.

5. **Open the dashboard**  
   Open your browser and type in the address bar (do **not** search Google):
   ```
   http://localhost:8000
   ```

6. **Log in**

   **MT5 account:**
   - Make sure MetaTrader 5 is running **and logged in** on this computer
   - Enter your account number (Login), password, and server name
     > 💡 Don't know your server name? In MT5 go to **File → Open Account** — the server name is listed next to your broker on the account list
   - Click **Połącz z MT5**

   **cTrader account:**
   - Switch to the **cTrader** tab in the login form
   - Enter the **Client ID** and **Client Secret** you copied from Spotware Connect (see section above)
   - Click **Autoryzuj** — a Spotware login page will open in your browser
   - Log in with your Spotware account
   - Return to the dashboard — your accounts will load automatically. Select one and click **Połącz**
   - The app routes to the proper cTrader endpoint automatically based on selected account type (**LIVE/DEMO**)

---

### Troubleshooting

**The console window closed immediately after double-clicking `start_server.bat`**  
Python is likely not installed or was not added to PATH. Re-run `install.bat` and read the error messages carefully.

**The dashboard doesn't open / browser shows "This site can't be reached"**  
Make sure `start_server.bat` is still running (the console window must stay open). Type `http://localhost:8000` manually in the browser's address bar — do not use the search bar.

**MT5 connection fails**  
Check that MetaTrader 5 is open **and logged in** on the same computer. Make sure the server name is correct — find it in MT5 under **File → Open Account**.

**cTrader — no accounts appear after authorization**  
You need to link your account in Spotware Connect first. See [Getting cTrader Client ID & Secret](#getting-ctrader-client-id--secret) steps 5–7.

**cTrader support is unavailable / package import errors (Twisted, ProtoOAErrorRes, EndPoints, etc.)**  
Install Microsoft C++ Build Tools, then run:
```powershell
.venv\Scripts\python.exe -m pip install -r mt5_server\requirements-ctrader.txt
```

---

### Stopping the server

Close the `start_server.bat` console window, or press `Ctrl+C` inside it.

---

### Notes

- All data is processed **locally** on your computer — nothing is sent to external servers
- MT5 requires the MetaTrader 5 terminal to be running and **logged in** on the **same machine** as the server
- cTrader connects via the Spotware cloud API — no terminal needed, but internet is required
- The investor (read-only) password is recommended for MT5 — the app does not execute trades

---

---

## 🇵🇱 Polski

### Funkcje

| Funkcja | Opis |
|---|---|
| 📊 **Podgląd konta na żywo** | Saldo, equity, depozyt, floating P&L |
| 📋 **Otwarte pozycje** | Wszystkie otwarte transakcje z ceną otwarcia, aktualną, swapem, P&L |
| 📈 **Pełne statystyki** | Win rate, profit factor, Sharpe ratio, Z-Score, expectancy, drawdown i więcej |
| 📅 **Miesięczny kalendarz P&L** | Kalendarz w stylu Myfxbook z zyskami/stratami każdego dnia |
| 📉 **Krzywa equity** | Pełny wykres historii salda od otwarcia konta |
| 🎨 **Motywy** | Ciemny / Jasny (kolory Myfxbook) / Własny |
| 👁️ **Widoczność paneli** | Pokaż/ukryj każdy panel osobno |
| 🔗 **Obsługa MT5** | Łączy się z lokalnym terminalem MetaTrader 5 (hasło inwestora) |
| 🔗 **Obsługa cTrader** | Łączy się przez Spotware OAuth2 (terminal nie jest potrzebny) |

---

### Wymagania

- **Windows 10 / 11** (64-bit)
- **Python 3.11 lub nowszy** — pobierz ze strony [python.org](https://www.python.org/downloads/)  
  ⚠️ Podczas instalacji zaznacz **"Add Python to PATH"**
- **Terminal MetaTrader 5** — uruchomiony i **zalogowany** na konto *(tylko dla kont MT5)*  
  ⚠️ Sam otwarty MT5 nie wystarczy — musisz być zalogowany na konto tradingowe
- Połączenie z internetem *(tylko dla kont cTrader)*
- Dla **obsługi cTrader na Windows**: najpierw zainstaluj **Microsoft C++ Build Tools**, potem uruchom `install.bat`  
  https://visualstudio.microsoft.com/visual-cpp-build-tools/

---

### Jak uzyskać Client ID i Client Secret dla cTrader?

> ⚠️ **Użytkownicy cTrader: wykonaj tę sekcję przed instalacją.** Client ID i Client Secret będą potrzebne w kroku 6.

1. Wejdź na [connect.spotware.com](https://connect.spotware.com) i zaloguj się (te same dane co w platformie cTrader)
2. Kliknij **Applications** → **New Application**
3. Wpisz dowolną nazwę (np. `MyMonitor`), a w polu Redirect URI wpisz dokładnie:
   ```
   http://localhost:8000/auth/ctrader/callback
   ```
4. Zapisz — zobaczysz swój **Client ID** i **Client Secret**. Skopiuj je w bezpieczne miejsce.

**Powiązanie konta cTrader z aplikacją:**

5. W panelu Spotware Connect otwórz swoją nowo utworzoną aplikację i kliknij zakładkę **Accounts**
6. Kliknij **Add Account** i wpisz numer swojego konta cTrader
   > 💡 Numer konta cTrader widoczny jest w lewym górnym rogu platformy cTrader po zalogowaniu — to ciąg cyfr (np. `12345678`)
7. Możesz dodać kilka kont — wszystkie będą dostępne w selektorze kont w dashboardzie po autoryzacji
   > 💡 W aplikacji konta są oznaczone jako **LIVE/DEMO**. Wybierz właściwe przed połączeniem.

> 💡 Jeśli pominiesz kroki 5–7, po zalogowaniu pojawią się tylko konta przypisane przez brokera.

---

### Instalacja — krok po kroku

> 💡 **Użytkownicy cTrader:** Przed krokiem 6 upewnij się, że wykonałeś już sekcję [Jak uzyskać Client ID i Client Secret](#jak-uzyska-client-id-i-client-secret-dla-ctrader) powyżej.

1. **Pobierz projekt**  
   Wejdź na [stronę projektu na GitHub](https://github.com/Kacperpe/StockMarketCalendar), kliknij zielony przycisk **Code** → **Download ZIP**, a następnie wypakuj folder w dowolne miejsce (np. `C:\MT5Monitor`).

2. **Uruchom instalator**  
   Kliknij dwa razy plik `install.bat` (albo od razu `start_server.bat` - uruchomi instalator automatycznie, jeśli trzeba).  
   Instalator automatycznie:
   - Sprawdzi, czy Python jest zainstalowany
   - Przygotuje izolowane środowisko dla aplikacji (nie musisz wiedzieć co to znaczy)
   - Przeskanuje zainstalowane pakiety i doinstaluje tylko brakujące lub niezgodne wersje
   - Zainstaluje wszystkie wymagane pakiety
   - Utworzy domyślny plik konfiguracyjny `mt5_server\.env`

3. **Konfiguracja** *(opcjonalnie)*  
   Otwórz plik `mt5_server\.env` w Notatniku i ustaw `API_KEY` na dowolny losowy ciąg znaków.  
   Login/hasło/serwer MT5 możesz też wpisać bezpośrednio w przeglądarce.

4. **Uruchom serwer**  
   Kliknij dwa razy plik `start_server.bat`.  
   Pojawi się okno konsoli — nie zamykaj go podczas korzystania z aplikacji.

5. **Otwórz dashboard**  
   Otwórz przeglądarkę i wpisz w pasek adresu (NIE szukaj w Google):
   ```
   http://localhost:8000
   ```

6. **Zaloguj się**

   **Konto MT5:**
   - Upewnij się, że MetaTrader 5 jest uruchomiony i **zalogowany** na tym komputerze
   - Wpisz numer konta (Login), hasło oraz nazwę serwera
     > 💡 Nie wiesz jak się nazywa serwer? W MT5 kliknij **Plik → Otwórz konto** — nazwa serwera widoczna jest na liście obok Twojego konta
   - Kliknij **Połącz z MT5**

   **Konto cTrader:**
   - Przełącz się na zakładkę **cTrader** w formularzu logowania
   - Wpisz **Client ID** i **Client Secret** skopiowane ze Spotware Connect (patrz sekcja powyżej)
   - Kliknij **Autoryzuj** — w przeglądarce otworzy się strona logowania Spotware
   - Zaloguj się swoim kontem Spotware
   - Wróć do dashboardu — konta załadują się automatycznie. Wybierz konto i kliknij **Połącz**
   - Aplikacja automatycznie wybierze właściwy endpoint cTrader na podstawie typu konta (**LIVE/DEMO**)

---

### Rozwiązywanie problemów

**Okno konsoli zamknęło się od razu po kliknięciu `start_server.bat`**  
Najprawdopodobniej Python nie jest zainstalowany lub nie został dodany do PATH. Uruchom ponownie `install.bat` i uważnie przeczytaj komunikaty błędów.

**Dashboard się nie otwiera / przeglądarka pokazuje „Nie można połączyć się z witryną"**  
Upewnij się, że `start_server.bat` nadal działa (okno konsoli musi być otwarte). Wpisz `http://localhost:8000` ręcznie w pasek adresu — nie używaj paska wyszukiwania.

**MT5 nie łączy się**  
Sprawdź, czy MetaTrader 5 jest otwarty **i zalogowany** na tym samym komputerze. Upewnij się, że wpisujesz poprawną nazwę serwera (widoczna w MT5 pod **Plik → Otwórz konto**).

**cTrader — po autoryzacji nie pojawiają się żadne konta**  
Musisz najpierw przypisać konto w panelu Spotware Connect. Zobacz sekcję [Jak uzyskać Client ID i Client Secret](#jak-uzyska-client-id-i-client-secret-dla-ctrader) — szczególnie kroki 5–7.

**Obsługa cTrader jest niedostępna / błędy importu pakietów (Twisted, ProtoOAErrorRes, EndPoints itp.)**  
Zainstaluj Microsoft C++ Build Tools, a następnie uruchom:
```powershell
.venv\Scripts\python.exe -m pip install -r mt5_server\requirements-ctrader.txt
```

---

### Zatrzymanie serwera

Zamknij okno konsoli `start_server.bat` lub naciśnij `Ctrl+C` wewnątrz niego.

---

### Uwagi

- Wszystkie dane są przetwarzane **lokalnie** na Twoim komputerze — nic nie jest wysyłane na zewnętrzne serwery
- MT5 wymaga, aby terminal MetaTrader 5 działał i był **zalogowany** na **tym samym** komputerze co serwer
- cTrader łączy się przez chmurę Spotware — terminal nie jest potrzebny, ale wymagany jest internet
- Zalecane jest hasło inwestora (tylko do odczytu) dla MT5 — aplikacja nie wykonuje transakcji

---

## 🏷️ Creating a Release

Releases are created automatically by a GitHub Actions workflow whenever a version tag is pushed.

**Steps to publish a new release:**

1. Update the `VERSION` file in the repository root with the new version number (e.g. `1.2.0`).
2. Commit and push the change to `main`.
3. Create and push a matching Git tag:
   ```bash
   git tag v1.2.0
   git push origin v1.2.0
   ```
4. The workflow (`.github/workflows/release.yml`) will automatically:
   - Build a ZIP archive of the project
   - Create a GitHub Release named `v1.2.0`
   - Attach the ZIP as a downloadable release asset

Tags must follow the `vMAJOR.MINOR.PATCH` format (e.g. `v1.0.0`, `v1.2.3`).

---

*Built with FastAPI · Chart.js · MetaTrader5 Python · cTrader Open API*
