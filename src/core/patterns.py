from typing import List, Optional, Tuple

from src.data.models import Candle, MarketState


def _sma(values: List[float], window: int) -> float:
    if len(values) < window:
        window = len(values)
    return sum(values[-window:]) / float(window) if window > 0 else 0.0


def infer_trend(candles: List[Candle], ma_window: int = 10) -> MarketState:
    """Infer trend using a simple moving average and net price direction.
    - BULLISH if last close > SMA and net up vs a few bars ago.
    - BEARISH if last close < SMA and net down vs a few bars ago.
    - Else RANGE.
    """
    if not candles:
        return MarketState.RANGE

    closes = [c.close for c in candles]
    highs = [c.high for c in candles]
    lows = [c.low for c in candles]

    sma_val = _sma(closes, ma_window)
    last_close = closes[-1]

    ref_idx = -2 if len(closes) >= 2 else 0
    net_up = last_close > closes[ref_idx]
    net_down = last_close < closes[ref_idx]

    if last_close > sma_val and net_up:
        return MarketState.BULLISH
    if last_close < sma_val and net_down:
        return MarketState.BEARISH
    return MarketState.RANGE


def detect_double_top(
    candles: List[Candle],
    lookback: int = 8,
    tolerance_pct: float = 0.002,  # 0.2%
) -> Tuple[bool, Optional[int], Optional[float]]:
    """Detect a double-top pattern ending with a rejection candle.
    Returns (is_double_top, rejection_index, reference_high).
    - Finds a prior swing high and a second high within tolerance.
    - Rejection: last candle closes below open and prints near the high region.
    """
    n = len(candles)
    if n < 4:
        return False, None, None

    window = candles[-lookback:] if n >= lookback else candles
    highs = [c.high for c in window]
    # First swing high index within window
    first_idx = highs.index(max(highs[:-1])) if len(highs) > 1 else 0
    first_high = highs[first_idx]

    # Second peak at the last candle's high (retest + rejection)
    second_high = window[-1].high

    # Are the highs close enough?
    close_enough = abs(second_high - first_high) / max(1.0, first_high) <= tolerance_pct

    # Rejection on last candle
    last = window[-1]
    rejection = last.close < last.open and (last.high >= second_high or last.high >= first_high)

    if close_enough and rejection:
        # Return index relative to full candles list
        rejection_index = n - 1
        return True, rejection_index, max(first_high, second_high)
    return False, None, None


def detect_double_bottom(
    candles: List[Candle],
    lookback: int = 8,
    tolerance_pct: float = 0.002,  # 0.2%
) -> Tuple[bool, Optional[int], Optional[float]]:
    """Detect a double-bottom pattern ending with a rejection candle.
    Returns (is_double_bottom, rejection_index, reference_low).
    - Finds a prior swing low and a second low within tolerance.
    - Rejection: last candle closes above open near the low region.
    """
    n = len(candles)
    if n < 4:
        return False, None, None

    window = candles[-lookback:] if n >= lookback else candles
    lows = [c.low for c in window]
    first_idx = lows.index(min(lows[:-1])) if len(lows) > 1 else 0
    first_low = lows[first_idx]

    second_idx = len(window) - 2
    second_low = lows[second_idx]

    close_enough = abs(second_low - first_low) / max(1.0, second_low) <= tolerance_pct

    last = window[-1]
    rejection = last.close > last.open and (last.low <= second_low or last.low <= first_low)

    if close_enough and rejection:
        rejection_index = n - 1
        return True, rejection_index, min(first_low, second_low)
    return False, None, None
