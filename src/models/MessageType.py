from enum import Enum


class MessageType(Enum):
    TRADINGVIEW = 1,
    ERROR = 2,
    CONFIRMATION = 3
    CANCELLED = 4
    INFO = 5
