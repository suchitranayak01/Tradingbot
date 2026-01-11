from dataclasses import dataclass
from typing import Dict, List, Optional

from src.data.models import Candle, OIData, FuturesOI, MarketState
from src.core.patterns import infer_trend, detect_double_top, detect_double_bottom
from src.core.oi_analysis import (
    atm_call_oi_rising,
    atm_put_oi_rising,
    combined_futures_oi_change,
)


@dataclass
class Signal:
    timestamp: str
    action: str  # "sell_iron_condor" | "no_trade"
    context: Dict[str, str]
    call_distance: Optional[int] = None
    put_distance: Optional[int] = None
    hedge_distance: int = 900  # Distance for protective buy legs
    capital_deployed: float = 0.0  # Estimated capital for SL calculation


class NonDirectionalStrangleStrategy:
    def __init__(
        self,
        tolerance_pct: float = 0.002,
        min_oi_change_pct: float = 0.0,
        fut_min_drop_pct: float = 0.01,
    ) -> None:
        self.tolerance_pct = tolerance_pct
        self.min_oi_change_pct = min_oi_change_pct
        self.fut_min_drop_pct = fut_min_drop_pct

    def evaluate(self, candles: List[Candle], oi: List[OIData], fut: List[FuturesOI]) -> Optional[Signal]:
        if not candles or not oi or not fut:
            return None

        trend = infer_trend(candles)
        ts = candles[-1].timestamp

        bull_dt, _, _ = detect_double_top(candles, tolerance_pct=self.tolerance_pct)
        bear_db, _, _ = detect_double_bottom(candles, tolerance_pct=self.tolerance_pct)

        call_rising = atm_call_oi_rising(oi, min_pct=self.min_oi_change_pct)
        put_rising = atm_put_oi_rising(oi, min_pct=self.min_oi_change_pct)
        fut_dropping, fut_had_rise = combined_futures_oi_change(
            fut, min_drop_pct=self.fut_min_drop_pct
        )

        # Situation handling for bullish trend
        if trend == MarketState.BULLISH:
            if bull_dt:
                if not call_rising and not fut_dropping:
                    return Signal(
                        timestamp=ts,
                        action="no_trade",
                        context={
                            "reason": "Double-top false; ATM call OI falling and futures OI stable",
                            "situation": "1",
                        },
                    )
                if call_rising and not fut_dropping:
                    return Signal(
                        timestamp=ts,
                        action="sell_iron_condor",
                        context={
                            "reason": "Double-top + rising ATM call OI",
                            "situation": "2",
                        },
                        call_distance=100,
                        put_distance=100,
                        hedge_distance=900,
                    )
                if call_rising and fut_dropping:
                    return Signal(
                        timestamp=ts,
                        action="sell_iron_condor",
                        context={
                            "reason": "Double-top + rising ATM call OI + futures OI drop (long unwinding)",
                            "situation": "3",
                        },
                        call_distance=75,
                        put_distance=125,
                        hedge_distance=900,
                    )
            # If no pattern or confirmations, avoid trade
            return None

        # Situation handling for bearish trend (analogs)
        if trend == MarketState.BEARISH:
            if bear_db:
                if not put_rising and not fut_dropping:
                    return Signal(
                        timestamp=ts,
                        action="no_trade",
                        context={
                            "reason": "Double-bottom false; ATM put OI falling and futures OI stable",
                            "situation": "1B",
                        },
                    )
                if put_rising and not fut_dropping:
                    return Signal(
                        timestamp=ts,
                        action="sell_iron_condor",
                        context={
                            "reason": "Double-bottom + rising ATM put OI",
                            "situation": "2B",
                        },
                        call_distance=100,
                        put_distance=100,
                        hedge_distance=900,
                    )
                if put_rising and fut_dropping:
                    return Signal(
                        timestamp=ts,
                        action="sell_iron_condor",
                        context={
                            "reason": "Double-bottom + rising ATM put OI + futures OI drop",
                            "situation": "3B",
                        },
                        call_distance=125,
                        put_distance=75,
                        hedge_distance=900,
                    )
            return None

        # Range: no trade by default
        return None
