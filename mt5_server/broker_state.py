"""
Central broker state — tracks which broker (MT5 / cTrader) is currently active
and provides a unified snapshot getter used by all API routes.
"""

BROKER_MT5 = "mt5"
BROKER_CT  = "ctrader"

_active_broker: str = BROKER_MT5


def set_broker(broker: str) -> None:
    global _active_broker
    assert broker in (BROKER_MT5, BROKER_CT)
    _active_broker = broker


def get_broker() -> str:
    return _active_broker


def is_mt5() -> bool:
    return _active_broker == BROKER_MT5


def is_ct() -> bool:
    return _active_broker == BROKER_CT
