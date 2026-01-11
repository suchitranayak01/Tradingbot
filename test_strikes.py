#!/usr/bin/env python3
import pandas as pd
from src.strategies.non_directional_strangle import NonDirectionalStrangleStrategy
from src.data.models import Candle, OIData, FuturesOI

candles_df = pd.read_csv('examples/data/candles.csv')
oi_df = pd.read_csv('examples/data/oi.csv')
fut_df = pd.read_csv('examples/data/futures_oi.csv')

candles = [Candle(str(r.timestamp), float(r.open), float(r.high), float(r.low), float(r.close)) for r in candles_df.itertuples(index=False)]
oi = [OIData(str(r.timestamp), float(r.oi_call_atm), float(r.oi_put_atm)) for r in oi_df.itertuples(index=False)]
fut = [FuturesOI(str(r.timestamp), float(r.current_month_oi), float(r.next_month_oi)) for r in fut_df.itertuples(index=False)]

strat = NonDirectionalStrangleStrategy()
for i in range(4, len(candles) + 1):
    sig = strat.evaluate(candles[:i], oi[:i], fut[:i])
    if sig:
        spot = candles[i-1].close
        print(f'\nSignal detected!')
        print(f'Spot Price: {spot}')
        print(f'')
        print(f'BUY  Call at:  {int(spot + 900)} (900 points away) | SELL Call at: {int(spot + sig.call_distance)} (closer)')
        print(f'BUY  Put at:   {int(spot - 900)} (900 points away) | SELL Put at:  {int(spot - sig.put_distance)} (closer)')
        print(f'')
        print(f'Reason: {sig.context.get("reason")}')

