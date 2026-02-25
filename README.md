# MonitoringTradingu MVP (skeleton)

Szkielet aplikacji zgodny z Twoją specyfikacją MVP:

- `frontend`: Next.js + TypeScript (ekrany: login/register/accounts/overview/pnl/trades)
- `backend`: FastAPI (auth, accounts, data endpoints, MT5 ingest HMAC)
- `postgres`: dane
- `redis`: cache/kolejka
- `worker`: Celery placeholder pod sync/agregacje
- `proxy`: Nginx (routing `/api` -> backend, reszta -> frontend)

## Co już działa

- Rejestracja / logowanie / refresh JWT
- CRUD podstawowy kont tradingowych (lista, dodanie, szczegóły)
- `connect/mt5` (generuje `ingest_key`, zwraca instrukcje do EA)
- `connect/ctrader` (placeholder start OAuth URL)
- Endpointy danych:
  - `/api/accounts/{id}/trades`
  - `/api/accounts/{id}/daily-metrics`
  - `/api/accounts/{id}/equity-curve`
  - `/api/accounts/{id}/stats`
- MT5 ingest:
  - `/api/ingest/mt5/snapshot`
  - HMAC (`X-Signature`, `X-Timestamp`, `X-Nonce`)
  - upsert po `(account_id, provider_trade_id)`
  - przeliczenie `daily_account_metrics` po imporcie deali

## Ważne ograniczenia obecnego skeletonu

- `account_credentials.encrypted_payload` jest na razie tylko serializowane jako JSON bytes (bez realnego szyfrowania)
- brak pełnego flow OAuth cTrader (callback/token refresh/rate limiting)
- brak trwałych snapshotów balance/equity (equity curve liczone fallbackiem z zamkniętych trade'ów)
- brak scheduler beat/cron dla workera
- `daily metrics` z ingestu liczone globalnie dla konta (działa w MVP, można zoptymalizować do "impacted days only")

## Uruchomienie (Docker Compose)

1. Skopiuj `.env.example` do `.env`
2. Uruchom:

```bash
docker compose up --build
```

3. Wejdź:
- UI: `http://localhost`
- Backend docs: `http://localhost/api/docs`
- Health: `http://localhost/healthz`

## Struktura

- `docker-compose.yml`
- `backend/app/main.py`
- `backend/app/api/routes/`
- `backend/app/models/`
- `backend/sql/001_init.sql`
- `frontend/app/`
- `worker/app.py`
- `proxy/nginx.conf`

## Mapowanie na Twój plan realizacji

1. Fundamenty: `auth`, `accounts`, DB, Docker -> zrobione (skeleton)
2. Dashboard bez integracji -> częściowo zrobione (mock UI)
3. MT5 ingest + trades + daily metrics -> zrobione bazowo
4. Equity curve + stats + PnL calendar -> endpointy są, UI mock
5. cTrader OAuth + sync -> placeholder connect URL, brak callback/sync
6. Hardening -> do zrobienia

## Najbliższe sensowne kroki

1. Dodać prawdziwe szyfrowanie `account_credentials` (np. Fernet/KMS)
2. Dodać callback OAuth cTrader + token refresh w workerze
3. Dodać tabelę snapshotów `account_state_snapshots` i prawdziwy equity curve
4. Podłączyć frontend do API (auth + fetch danych)
5. Dodać migracje (Alembic) zamiast `create_all`
