import MetaTrader5 as mt5
import logging
import time

logger = logging.getLogger(__name__)


def connect_dynamic(login: int, password: str, server: str,
                    retries: int = 3, backoff: float = 1.5) -> bool:
    """Łączy z MT5 przy użyciu danych podanych przez użytkownika (np. hasło investor)."""
    for attempt in range(1, retries + 1):
        try:
            if not mt5.initialize():
                raise RuntimeError(f"initialize() failed: {mt5.last_error()}")

            if not mt5.login(login=login, password=password, server=server):
                raise RuntimeError(f"login() failed: {mt5.last_error()}")

            info = mt5.account_info()
            logger.info(f"MT5 connected: {info.name if info else 'unknown'}")
            return True

        except Exception as e:
            logger.warning(f"Attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(backoff * attempt)

    logger.error("MT5 connection failed after all retries")
    return False


def is_connected() -> bool:
    return mt5.account_info() is not None


def ensure_connected() -> bool:
    """Sprawdza połączenie; jeśli zerwane, reinicjalizuje terminal (bez ponownego logowania)."""
    if not is_connected():
        logger.warning("MT5 disconnected — reinitializing terminal...")
        mt5.shutdown()
        time.sleep(1)
        return mt5.initialize()
    return True


def disconnect():
    mt5.shutdown()
    logger.info("MT5 disconnected")

