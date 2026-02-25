CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(320) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TYPE broker_provider AS ENUM ('MT5', 'CTrader');
CREATE TYPE account_status AS ENUM ('new', 'active', 'error', 'disconnected');
CREATE TYPE trade_side AS ENUM ('buy', 'sell');
CREATE TYPE trade_status AS ENUM ('open', 'closed');
CREATE TYPE trade_record_type AS ENUM ('deal', 'order');

CREATE TABLE IF NOT EXISTS broker_accounts (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider broker_provider NOT NULL,
    name VARCHAR(120) NOT NULL,
    currency VARCHAR(16) NOT NULL,
    status account_status NOT NULL DEFAULT 'new',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS account_credentials (
    account_id BIGINT PRIMARY KEY REFERENCES broker_accounts(id) ON DELETE CASCADE,
    encrypted_payload BYTEA NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trades (
    id UUID PRIMARY KEY,
    account_id BIGINT NOT NULL REFERENCES broker_accounts(id) ON DELETE CASCADE,
    provider_trade_id VARCHAR(128) NOT NULL,
    symbol VARCHAR(64) NOT NULL,
    side trade_side NOT NULL,
    volume NUMERIC(20,8) NOT NULL,
    open_time TIMESTAMPTZ NOT NULL,
    close_time TIMESTAMPTZ NULL,
    open_price NUMERIC(20,10) NOT NULL,
    close_price NUMERIC(20,10) NULL,
    commission NUMERIC(20,8) NOT NULL DEFAULT 0,
    swap NUMERIC(20,8) NOT NULL DEFAULT 0,
    fees NUMERIC(20,8) NOT NULL DEFAULT 0,
    pnl NUMERIC(20,8) NOT NULL DEFAULT 0,
    status trade_status NOT NULL,
    record_type trade_record_type NOT NULL DEFAULT 'deal',
    magic BIGINT NULL,
    comment VARCHAR(255) NULL,
    raw_json JSONB NULL,
    CONSTRAINT uq_trades_account_provider_trade_id UNIQUE (account_id, provider_trade_id)
);

CREATE TABLE IF NOT EXISTS daily_account_metrics (
    account_id BIGINT NOT NULL REFERENCES broker_accounts(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    realized_pnl NUMERIC(20,8) NOT NULL DEFAULT 0,
    commissions NUMERIC(20,8) NOT NULL DEFAULT 0,
    swaps NUMERIC(20,8) NOT NULL DEFAULT 0,
    fees NUMERIC(20,8) NOT NULL DEFAULT 0,
    net_pnl NUMERIC(20,8) NOT NULL DEFAULT 0,
    end_balance NUMERIC(20,8) NULL,
    end_equity NUMERIC(20,8) NULL,
    PRIMARY KEY (account_id, date)
);

CREATE INDEX IF NOT EXISTS ix_trades_account_close_time ON trades(account_id, close_time);
CREATE INDEX IF NOT EXISTS ix_trades_account_symbol ON trades(account_id, symbol);
CREATE INDEX IF NOT EXISTS ix_daily_account_metrics_account_date ON daily_account_metrics(account_id, date);

