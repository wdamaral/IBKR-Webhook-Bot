from datetime import datetime

from pydantic import BaseModel, validator


class TradingViewOrder(BaseModel):
    secret: str = None
    ticker: str = None
    price: float | int = 0
    quantity: float | int = 0
    orderDate: datetime
    orderAction: str = None
    currentPositionSize: float | int = 0
    currentPositionType: str = None
    previousPositionSize: float | int = 0
    previousPositionType: str = None
