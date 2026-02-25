import enum


class BrokerProvider(str, enum.Enum):
    MT5 = "MT5"
    CTRADER = "CTrader"


class AccountStatus(str, enum.Enum):
    NEW = "new"
    ACTIVE = "active"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class TradeSide(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


class TradeStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


class TradeRecordType(str, enum.Enum):
    DEAL = "deal"
    ORDER = "order"

