# 📈 MT5 & cTrader Monitor

A real-time trading account dashboard for **MetaTrader 5** and **cTrader** accounts.  
Monitor your balance, open positions, performance statistics, and P&L calendar — all in one browser tab.

---

## 📋 Table of Contents / Spis treści

- 🇬🇧 **English**
  - [Features](#features)
  - [Requirements](#requirements)
  - [Installation — step by step](#installation--step-by-step)
  - [Getting cTrader Client ID & Secret](#getting-ctrader-client-id--secret)
  - [Stopping the server](#stopping-the-server)
  - [Notes](#notes)

- 🇵🇱 **Polski**
  - [Funkcje](#funkcje)
  - [Wymagania](#wymagania)
  - [Instalacja — krok po kroku](#instalacja--krok-po-kroku)
  - [Jak uzyskać Client ID i Client Secret dla cTrader?](#jak-uzyska-client-id-i-client-secret-dla-ctrader)
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
- **MetaTrader 5 terminal** running *(only for MT5 accounts)*
- Internet connection *(only for cTrader accounts)*

---

### Installation — step by step

1. **Download the project**  
   Click the green **Code** → **Download ZIP** button on GitHub, then extract the folder anywhere (e.g. `C:\MT5Monitor`).

2. **Run the installer**  
   Double-click `install.bat`.  
   It will:
   - Check that Python is installed
   - Create a virtual environment (`.venv`)
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
   - Make sure MetaTrader 5 is running on your computer
   - Enter your account number (Login), password, and server name
   - Click **Połącz z MT5**

   **cTrader account:**
   - Switch to the **cTrader** tab in the login form
   - Enter your **Client ID** and **Client Secret** from [Spotware Connect](https://connect.spotware.com)
   - Click **Autoryzuj** — a Spotware login page will open
   - Log in with your Spotware ID
   - Return to the dashboard, select your account, click **Połącz**

---

### Getting cTrader Client ID & Secret

1. Go to [connect.spotware.com](https://connect.spotware.com) and log in
2. Click **Applications** → **New Application**
3. Fill in any name, set Redirect URI to: `http://localhost:8000/auth/ctrader/callback`
4. Copy the **Client ID** and **Client Secret** — paste them in the login form

**Linking your cTrader trading account to the application:**

5. In the Spotware Connect panel, go to your application and click the **Accounts** tab
6. Click **Add Account** and enter your cTrader account number (the numeric ID shown in your cTrader platform)
7. You can add multiple cTrader accounts — all of them will be available in the account selector after authorization

> 💡 If you skip step 5–6, only accounts that were added by your broker (the cTrader platform operator) will appear after OAuth login.

---

### Stopping the server

Close the `start_server.bat` console window, or press `Ctrl+C` inside it.

---

### Notes

- All data is processed **locally** on your computer — nothing is sent to external servers
- MT5 requires the MetaTrader 5 terminal to be running on the **same machine** as the server
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
- **Terminal MetaTrader 5** uruchomiony *(tylko dla kont MT5)*
- Połączenie z internetem *(tylko dla kont cTrader)*

---

### Instalacja — krok po kroku

1. **Pobierz projekt**  
   Kliknij zielony przycisk **Code** → **Download ZIP** na GitHub, a następnie wypakuj folder w dowolne miejsce (np. `C:\MT5Monitor`).

2. **Uruchom instalator**  
   Kliknij dwa razy plik `install.bat`.  
   Instalator automatycznie:
   - Sprawdzi, czy Python jest zainstalowany
   - Utworzy środowisko wirtualne (`.venv`)
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
   - Upewnij się, że MetaTrader 5 jest uruchomiony na tym komputerze
   - Wpisz numer konta (Login), hasło oraz nazwę serwera
   - Kliknij **Połącz z MT5**

   **Konto cTrader:**
   - Przełącz się na zakładkę **cTrader** w formularzu logowania
   - Wpisz swój **Client ID** i **Client Secret** ze strony [Spotware Connect](https://connect.spotware.com)
   - Kliknij **Autoryzuj** — otworzy się strona logowania Spotware
   - Zaloguj się swoim kontem Spotware ID
   - Wróć do dashboardu, wybierz konto i kliknij **Połącz**

---

### Jak uzyskać Client ID i Client Secret dla cTrader?

1. Wejdź na [connect.spotware.com](https://connect.spotware.com) i zaloguj się
2. Kliknij **Applications** → **New Application**
3. Wpisz dowolną nazwę, w polu Redirect URI wpisz: `http://localhost:8000/auth/ctrader/callback`
4. Skopiuj **Client ID** i **Client Secret** — wklej je w formularz logowania

**Powiązanie konta cTrader z aplikacją:**

5. W panelu Spotware Connect przejdź do swojej aplikacji i kliknij zakładkę **Accounts**
6. Kliknij **Add Account** i wpisz numer swojego konta cTrader (numeryczny identyfikator widoczny w platformie cTrader)
7. Możesz dodać kilka kont — wszystkie będą dostępne w selektorze kont po autoryzacji

> 💡 Jeśli pominiesz kroki 5–6, po zalogowaniu przez OAuth pojawią się tylko konta, które zostały przypisane przez Twojego brokera (operatora platformy cTrader).

---

### Zatrzymanie serwera

Zamknij okno konsoli `start_server.bat` lub naciśnij `Ctrl+C` wewnątrz niego.

---

### Uwagi

- Wszystkie dane są przetwarzane **lokalnie** na Twoim komputerze — nic nie jest wysyłane na zewnętrzne serwery
- MT5 wymaga, aby terminal MetaTrader 5 działał na **tym samym** komputerze co serwer
- cTrader łączy się przez chmurę Spotware — terminal nie jest potrzebny, ale wymagany jest internet
- Zalecane jest hasło inwestora (tylko do odczytu) dla MT5 — aplikacja nie wykonuje transakcji

---

*Built with FastAPI · Chart.js · MetaTrader5 Python · cTrader Open API*
