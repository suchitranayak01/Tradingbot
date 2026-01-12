"""
Trending Stock Screener
Identifies stocks with strong trends and high volume for intraday trading.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class TrendingStockScreener:
    """Screen for trending stocks with high volume."""
    
    def __init__(
        self,
        min_volume_increase_pct: float = 50.0,  # Volume 50% above average
        min_price_change_pct: float = 2.0,      # At least 2% price move
        min_avg_volume: int = 100000,           # Minimum average volume
        lookback_days: int = 20,                # Lookback period for averages
    ):
        self.min_volume_increase_pct = min_volume_increase_pct
        self.min_price_change_pct = min_price_change_pct
        self.min_avg_volume = min_avg_volume
        self.lookback_days = lookback_days
    
    def calculate_trend_strength(self, candles: List[Dict]) -> Optional[float]:
        """Calculate trend strength using RSI and price momentum."""
        if not candles or len(candles) < 14:
            return None
        
        try:
            closes = [c['close'] for c in candles[-14:]]
            
            # Calculate RSI
            deltas = np.diff(closes)
            seed = deltas[:1]
            up = seed[seed >= 0].sum() / 14
            down = -seed[seed < 0].sum() / 14
            
            for d in deltas[1:]:
                if d >= 0:
                    up = (up * 13 + d) / 14
                    down = down * 13 / 14
                else:
                    up = up * 13 / 14
                    down = (down * 13 - d) / 14
            
            rs = up / down if down != 0 else 0
            rsi = 100 - 100 / (1 + rs)
            
            # Calculate momentum (price change)
            momentum = ((closes[-1] - closes[0]) / closes[0]) * 100
            
            # Combined score
            trend_score = (rsi + 50 + momentum) / 3
            return trend_score
        
        except Exception as e:
            logger.error(f"Error calculating trend strength: {e}")
            return None
    
    def screen_stock(
        self,
        symbol: str,
        current_price: float,
        current_volume: int,
        avg_volume: int,
        price_change_pct: float,
        trend_score: Optional[float] = None,
    ) -> Dict[str, any]:
        """
        Screen a single stock against criteria.
        
        Returns dict with screening results.
        """
        volume_ratio = ((current_volume - avg_volume) / avg_volume) * 100 if avg_volume > 0 else 0
        
        meets_volume = current_volume > self.min_avg_volume and volume_ratio >= self.min_volume_increase_pct
        meets_price_change = abs(price_change_pct) >= self.min_price_change_pct
        
        # Trend direction
        trend_direction = "UP" if price_change_pct > 0 else "DOWN"
        
        # Score calculation
        score = 0
        if meets_volume:
            score += 50
        if meets_price_change:
            score += 30
        if trend_score and trend_score > 50:
            score += 20
        
        result = {
            'symbol': symbol,
            'price': current_price,
            'price_change_pct': price_change_pct,
            'trend_direction': trend_direction,
            'current_volume': current_volume,
            'avg_volume': avg_volume,
            'volume_ratio': volume_ratio,
            'volume_increase_pct': volume_ratio,
            'trend_score': trend_score or 50,
            'screening_score': score,
            'meets_volume_criteria': meets_volume,
            'meets_price_criteria': meets_price_change,
            'qualifies': score >= 50,  # Qualifies if score >= 50
        }
        
        return result
    
    def rank_stocks(self, stocks: List[Dict]) -> pd.DataFrame:
        """
        Rank and sort stocks by screening score.
        
        Args:
            stocks: List of screening result dicts
        
        Returns:
            Sorted DataFrame
        """
        if not stocks:
            return pd.DataFrame()
        
        df = pd.DataFrame(stocks)
        
        # Sort by screening score (descending), then by volume ratio
        df = df.sort_values(
            by=['screening_score', 'volume_increase_pct'],
            ascending=[False, False]
        )
        
        return df


class IntraDayScreener:
    """Specialized screener for intraday trading opportunities."""
    
    def __init__(
        self,
        min_range_pct: float = 1.5,      # Daily range at least 1.5%
        min_volume_increase: float = 100.0,  # Volume 100% above average
        target_price_change: float = 3.0,   # Looking for 3%+ moves
    ):
        self.min_range_pct = min_range_pct
        self.min_volume_increase = min_volume_increase
        self.target_price_change = target_price_change
    
    def get_intraday_opportunities(self, stocks: List[Dict]) -> pd.DataFrame:
        """Filter stocks suitable for intraday trading."""
        candidates = []
        
        for stock in stocks:
            # Check if stock has sufficient daily range
            daily_range = stock.get('volume_increase_pct', 0)
            price_move = abs(stock.get('price_change_pct', 0))
            
            if daily_range >= self.min_volume_increase and price_move >= self.target_price_change / 2:
                candidates.append({
                    **stock,
                    'intraday_score': (
                        (daily_range / self.min_volume_increase * 50) +
                        (price_move / self.target_price_change * 50)
                    )
                })
        
        if not candidates:
            return pd.DataFrame()
        
        df = pd.DataFrame(candidates)
        return df.sort_values('intraday_score', ascending=False)
