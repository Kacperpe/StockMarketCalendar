from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Trading Monitoring API"
    api_prefix: str = "/api"
    database_url: str = "postgresql+psycopg://trading_user:trading_pass@postgres:5432/trading_monitor"
    redis_url: str = "redis://redis:6379/0"
    jwt_secret_key: str = "change-me"
    jwt_refresh_secret_key: str = "change-me-too"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    app_timezone: str = "Europe/Warsaw"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

