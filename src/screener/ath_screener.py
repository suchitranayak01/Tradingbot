"""
All-Time High (ATH) Stock Screener
Identifies stocks trading near or at all-time highs.
"""

import logging
from typing import List, Dict, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class ATHStockScreener:
    """Screen for stocks near all-time highs."""
    
    def __init__(
        self,
        ath_distance_pct: float = 5.0,   # Within 5% of ATH
        min_volume: int = 500000,        # Minimum volume
        min_price: float = 100.0,        # Minimum price level
    ):
        self.ath_distance_pct = ath_distance_pct
        self.min_volume = min_volume
        self.min_price = min_price
    
    def screen_stock(
        self,
        symbol: str,
        current_price: float,
        all_time_high: float,
        current_volume: int,
        avg_volume: int,
    ) -> Dict[str, any]:
        """
        Screen a stock for ATH proximity.
        
        Returns dict with screening results.
        """
        if all_time_high == 0:
            return {'symbol': symbol, 'qualifies': False, 'reason': 'No ATH data'}
        
        distance_from_ath = ((all_time_high - current_price) / all_time_high) * 100
        distance_from_ath_pct = ((all_time_high - current_price) / all_time_high) * 100
        
        # Calculate proximity score (0-100)
        if distance_from_ath_pct <= 0:
            proximity_score = 100  # At ATH or above
        elif distance_from_ath_pct <= self.ath_distance_pct:
            proximity_score = 100 - (distance_from_ath_pct / self.ath_distance_pct * 50)
        else:
            proximity_score = 0
        
        meets_volume = current_volume >= self.min_volume * 0.8  # At least 80% of target
        meets_price = current_price >= self.min_price
        meets_ath_criteria = distance_from_ath_pct <= self.ath_distance_pct
        
        # Momentum from ATH
        volume_ratio = (current_volume / avg_volume) if avg_volume > 0 else 1
        momentum_score = min(volume_ratio * 30, 30)  # Up to 30 points for volume
        
        total_score = proximity_score + momentum_score
        
        result = {
            'symbol': symbol,
            'current_price': current_price,
            'all_time_high': all_time_high,
            'distance_from_ath_pct': distance_from_ath_pct,
            'distance_from_ath_value': all_time_high - current_price,
            'current_volume': current_volume,
            'avg_volume': avg_volume,
            'volume_ratio': volume_ratio,
            'proximity_score': proximity_score,
            'momentum_score': momentum_score,
            'total_score': total_score,
            'meets_volume_criteria': meets_volume,
            'meets_price_criteria': meets_price,
            'meets_ath_criteria': meets_ath_criteria,
            'breakout_probability': proximity_score / 100,
            'qualifies': meets_ath_criteria and meets_volume,
        }
        
        return result
    
    def rank_stocks(self, stocks: List[Dict]) -> pd.DataFrame:
        """
        Rank stocks by ATH proximity and potential.
        
        Args:
            stocks: List of screening result dicts
        
        Returns:
            Sorted DataFrame
        """
        if not stocks:
            return pd.DataFrame()
        
        df = pd.DataFrame(stocks)
        
        # Filter qualifying stocks
        df = df[df['qualifies']]
        
        # Sort by distance from ATH (ascending - closest first)
        # Then by volume ratio (descending - higher volume first)
        df = df.sort_values(
            by=['distance_from_ath_pct', 'volume_ratio'],
            ascending=[True, False]
        )
        
        return df
    
    def get_breakout_candidates(self, stocks: List[Dict], score_threshold: float = 70.0) -> pd.DataFrame:
        """Get stocks most likely to break above ATH."""
        if not stocks:
            return pd.DataFrame()
        
        df = pd.DataFrame(stocks)
        
        # Filter by score and volume
        breakout_stocks = df[
            (df['total_score'] >= score_threshold) &
            (df['meets_volume_criteria'])
        ]
        
        return breakout_stocks.sort_values('total_score', ascending=False)


class ConsistentHighPerformer:
    """Identify stocks consistently trading near ATH."""
    
    def __init__(self, lookback_days: int = 252):
        """
        Initialize with lookback period.
        
        Args:
            lookback_days: Number of days to consider (default: 1 year = 252 trading days)
        """
        self.lookback_days = lookback_days
    
    def analyze_historical_strength(
        self,
        symbol: str,
        prices: List[float],
        current_price: float,
    ) -> Dict[str, any]:
        """
        Analyze how strong a stock has been historically.
        
        Args:
            symbol: Stock symbol
            prices: Historical prices (most recent last)
            current_price: Current price
        
        Returns:
            Analysis dict
        """
        if not prices:
            return {}
        
        prices = np.array(prices)
        historical_high = np.max(prices)
        historical_low = np.min(prices)
        avg_price = np.mean(prices)
        
        # Percentile rank
        above_avg = np.sum(prices <= current_price) / len(prices) * 100
        
        # Strength indicator
        if historical_high > 0:
            strength = (current_price - historical_low) / (historical_high - historical_low) * 100
        else:
            strength = 0
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'historical_high': historical_high,
            'historical_low': historical_low,
            'average_price': avg_price,
            'price_percentile': above_avg,
            'strength_score': strength,
            'trading_range': historical_high - historical_low,
            'distance_from_high': historical_high - current_price,
            'days_near_high': np.sum(prices >= (historical_high * 0.95)) if historical_high > 0 else 0,
            'consistency': 'High' if strength > 75 else 'Medium' if strength > 50 else 'Low',
        }
