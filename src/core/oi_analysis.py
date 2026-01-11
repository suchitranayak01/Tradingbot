from typing import List, Tuple

from src.data.models import OIData, FuturesOI


def atm_call_oi_rising(oi: List[OIData], min_pct: float = 0.0) -> bool:
    if len(oi) < 2:
        return False
    prev, last = oi[-2], oi[-1]
    if prev.oi_call_atm == 0:
        return last.oi_call_atm > prev.oi_call_atm
    pct = (last.oi_call_atm - prev.oi_call_atm) / prev.oi_call_atm
    return pct > min_pct


def atm_put_oi_rising(oi: List[OIData], min_pct: float = 0.0) -> bool:
    if len(oi) < 2:
        return False
    prev, last = oi[-2], oi[-1]
    if prev.oi_put_atm == 0:
        return last.oi_put_atm > prev.oi_put_atm
    pct = (last.oi_put_atm - prev.oi_put_atm) / prev.oi_put_atm
    return pct > min_pct


def combined_futures_oi_change(
    fut: List[FuturesOI],
    min_drop_pct: float = 0.01,  # 1%
    recent_rise_window: int = 5,
    min_recent_rise_pct: float = 0.01,
) -> Tuple[bool, bool]:
    """Return (is_dropping, had_recent_rise).
    - is_dropping: latest combined OI down by min_drop_pct vs previous.
    - had_recent_rise: any positive rise above min_recent_rise_pct in last window.
    """
    if len(fut) < 2:
        return False, False

    prev, last = fut[-2], fut[-1]
    prev_c, last_c = prev.combined, last.combined
    drop_pct = (prev_c - last_c) / prev_c if prev_c > 0 else 0.0
    is_dropping = drop_pct >= min_drop_pct

    # Recent rise check
    had_rise = False
    window = fut[-recent_rise_window:] if len(fut) >= recent_rise_window else fut
    for i in range(1, len(window)):
        a, b = window[i - 1].combined, window[i].combined
        if a == 0:
            continue
        pct = (b - a) / a
        if pct >= min_recent_rise_pct:
            had_rise = True
            break

    return is_dropping, had_rise
