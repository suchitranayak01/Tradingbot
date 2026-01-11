from dataclasses import dataclass
from enum import Enum
from typing import Optional


class MarketState(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    RANGE = "range"


@dataclass
class Candle:
    timestamp: str
    open: float
    high: float
    low: float
    close: float


@dataclass
class OIData:
    timestamp: str
    oi_call_atm: float
    oi_put_atm: float


@dataclass
class FuturesOI:
    timestamp: str
    current_month_oi: float
    next_month_oi: float

    @property
    def combined(self) -> float:
        return float(self.current_month_oi) + float(self.next_month_oi)
