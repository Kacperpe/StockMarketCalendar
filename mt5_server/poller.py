import asyncio
import logging
from collections import deque
from datetime import datetime

import MetaTrader5 as mt5

from config import settings
from data_parser import parse_account, parse_positions
from mt5_client import ensure_connected

logger = logging.getLogger(__name__)

# Globalny snapshot trzymany w pamięci
snapshot: dict = {}
snapshot_lock = asyncio.Lock()

# Seria czasowa equity/balance — max 500 punktów, próbkowanie co ~5 s
EQUITY_MAX   = 500
EQUITY_EVERY = 5          # sekund między próbkami
equity_history: deque = deque(maxlen=EQUITY_MAX)
_equity_counter = 0       # licznik ticków do próbkowania


async def polling_loop(ws_manager):
    """
    Jeden task robi polling MT5 co POLL_INTERVAL sekund.
    Wszystkie REST i WS czytają z tego snapshotu.
    """
    global _equity_counter
    while True:
        try:
            if not ensure_connected():
                await asyncio.sleep(5)
                continue

            info      = mt5.account_info()
            positions = mt5.positions_get()

            new_snapshot = {
                "account":   parse_account(info),
                "positions": parse_positions(positions),
                "timestamp": datetime.utcnow().isoformat(),
            }

            async with snapshot_lock:
                snapshot.clear()
                snapshot.update(new_snapshot)

            # Próbkuj equity co EQUITY_EVERY sekund
            _equity_counter += settings.POLL_INTERVAL
            if _equity_counter >= EQUITY_EVERY and info is not None:
                equity_history.append({
                    "ts":      datetime.utcnow().isoformat(),
                    "equity":  round(info.equity, 2),
                    "balance": round(info.balance, 2),
                    "pnl":     round(info.profit, 2),
                })
                _equity_counter = 0

            await ws_manager.broadcast(snapshot)

        except Exception as e:
            logger.error(f"Polling error: {e}", exc_info=True)

        await asyncio.sleep(settings.POLL_INTERVAL)


def get_snapshot() -> dict:
    return snapshot


def get_equity_history() -> list:
    return list(equity_history)
