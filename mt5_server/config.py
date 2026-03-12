from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # MT5 credentials are now provided via browser login — .env values are optional fallback
    MT5_LOGIN: Optional[int] = None
    MT5_PASSWORD: Optional[str] = None
    MT5_SERVER: Optional[str] = None
    API_KEY: str = ""          # legacy, no longer used
    POLL_INTERVAL: float = 1.0
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    # Set to True if you want the MT5 terminal to be initialised automatically when the server
    # starts.  Default is False so that cTrader-only users do not see MT5 launch on startup.
    AUTO_INIT_MT5: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
