"""
Options Analytics and Straddle Analysis
Analyze ATM straddles, implied volatility, and put-call ratios
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class StraddleAnalyzer:
    """Analyze ATM straddles (ATM Call + ATM Put)."""
    
    def __init__(self, underlying_price: float, strike_distance: int = 100):
        """
        Initialize straddle analyzer.
        
        Args:
            underlying_price: Current price of underlying
            strike_distance: Distance between strikes (e.g., 100 for NIFTY)
        """
        self.underlying_price = underlying_price
        self.strike_distance = strike_distance
    
    def get_atm_strike(self) -> int:
        """Get ATM (At The Money) strike."""
        atm = (self.underlying_price / self.strike_distance)
        return int(atm) * self.strike_distance
    
    def analyze_straddle(
        self,
        atm_call_price: float,
        atm_put_price: float,
        call_iv: float,
        put_iv: float,
    ) -> Dict[str, float]:
        """
        Analyze ATM straddle position.
        
        Args:
            atm_call_price: ATM call option price
            atm_put_price: ATM put option price
            call_iv: Implied volatility of call
            put_iv: Implied volatility of put
        
        Returns:
            Analysis dict
        """
        straddle_price = atm_call_price + atm_put_price
        avg_iv = (call_iv + put_iv) / 2
        
        # Straddle is profitable if underlying moves more than straddle cost
        # Breakeven points
        upper_breakeven = self.get_atm_strike() + straddle_price
        lower_breakeven = self.get_atm_strike() - straddle_price
        
        # Expected move (approx: stock price * IV * sqrt(days to expiry / 365))
        # For daily calculation, assume 1 day to move
        expected_daily_move = self.underlying_price * avg_iv / np.sqrt(365)
        
        return {
            'atm_strike': self.get_atm_strike(),
            'atm_call_price': atm_call_price,
            'atm_put_price': atm_put_price,
            'straddle_price': straddle_price,
            'call_iv': call_iv,
            'put_iv': put_iv,
            'avg_iv': avg_iv,
            'upper_breakeven': upper_breakeven,
            'lower_breakeven': lower_breakeven,
            'call_put_ratio': atm_call_price / atm_put_price if atm_put_price > 0 else 0,
            'expected_daily_move': expected_daily_move,
            'profit_range': {
                'upper': upper_breakeven,
                'lower': lower_breakeven,
                'range_width': upper_breakeven - lower_breakeven
            }
        }
    
    def calculate_straddle_payoff(
        self,
        spot_range: List[float],
        atm_strike: int,
        straddle_cost: float,
    ) -> pd.DataFrame:
        """
        Calculate P&L for straddle at different spot prices.
        
        Args:
            spot_range: Range of spot prices
            atm_strike: ATM strike price
            straddle_cost: Cost of straddle (call + put premium)
        
        Returns:
            DataFrame with payoff at different spots
        """
        payoffs = []
        
        for spot in spot_range:
            # Call payoff: max(spot - strike, 0)
            call_payoff = max(spot - atm_strike, 0)
            # Put payoff: max(strike - spot, 0)
            put_payoff = max(atm_strike - spot, 0)
            # Total payoff minus cost
            total_payoff = call_payoff + put_payoff - straddle_cost
            
            payoffs.append({
                'spot': spot,
                'call_payoff': call_payoff,
                'put_payoff': put_payoff,
                'total_payoff': total_payoff,
                'pnl': total_payoff,
            })
        
        return pd.DataFrame(payoffs)


class ImpliedVolatilityAnalyzer:
    """Analyze implied volatility across strikes and expiries."""
    
    @staticmethod
    def calculate_iv_skew(
        call_ivs: Dict[int, float],
        put_ivs: Dict[int, float],
        atm_strike: int,
    ) -> Dict[str, float]:
        """
        Calculate IV skew (difference between OTM and ATM IV).
        
        Args:
            call_ivs: Dict of strike -> call IV
            put_ivs: Dict of strike -> put IV
            atm_strike: ATM strike
        
        Returns:
            Skew analysis
        """
        call_iv_list = list(call_ivs.values()) if call_ivs else [0]
        put_iv_list = list(put_ivs.values()) if put_ivs else [0]
        
        atm_iv = (call_ivs.get(atm_strike, 0) + put_ivs.get(atm_strike, 0)) / 2
        avg_call_iv = np.mean(call_iv_list) if call_iv_list else 0
        avg_put_iv = np.mean(put_iv_list) if put_iv_list else 0
        
        return {
            'atm_iv': atm_iv,
            'avg_call_iv': avg_call_iv,
            'avg_put_iv': avg_put_iv,
            'call_put_iv_ratio': avg_call_iv / avg_put_iv if avg_put_iv > 0 else 0,
            'call_skew': max(call_iv_list) - min(call_iv_list) if call_iv_list else 0,
            'put_skew': max(put_iv_list) - min(put_iv_list) if put_iv_list else 0,
            'overall_skew': avg_put_iv - avg_call_iv,  # Positive = put skew
        }
    
    @staticmethod
    def iv_term_structure(
        near_month_iv: float,
        far_month_iv: float,
    ) -> Dict[str, any]:
        """
        Analyze IV term structure (front month vs back month).
        
        Args:
            near_month_iv: IV for near month expiry
            far_month_iv: IV for far month expiry
        
        Returns:
            Term structure analysis
        """
        if near_month_iv == 0:
            contango_backwardation = "Unknown"
            ratio = 0
        elif far_month_iv > near_month_iv:
            contango_backwardation = "Contango"  # IV rising with time
            ratio = (far_month_iv - near_month_iv) / near_month_iv * 100
        else:
            contango_backwardation = "Backwardation"  # IV declining with time
            ratio = (near_month_iv - far_month_iv) / near_month_iv * 100
        
        return {
            'near_month_iv': near_month_iv,
            'far_month_iv': far_month_iv,
            'structure': contango_backwardation,
            'iv_slope_pct': ratio,
            'interpretation': (
                "IV expected to increase with time" if contango_backwardation == "Contango"
                else "IV expected to decrease with time"
            )
        }


class PutCallRatioAnalyzer:
    """Analyze put-call ratios and market sentiment."""
    
    @staticmethod
    def calculate_pcr(
        put_volume: int,
        call_volume: int,
        put_oi: int = None,
        call_oi: int = None,
    ) -> Dict[str, float]:
        """
        Calculate put-call ratios (volume and OI based).
        
        Args:
            put_volume: Total put volume
            call_volume: Total call volume
            put_oi: Put open interest (optional)
            call_oi: Call open interest (optional)
        
        Returns:
            PCR analysis
        """
        result = {}
        
        # Volume based PCR
        if call_volume > 0:
            volume_pcr = put_volume / call_volume
            result['volume_pcr'] = volume_pcr
            result['volume_pcr_interpretation'] = (
                "Bullish" if volume_pcr < 0.7 else
                "Neutral" if volume_pcr < 1.3 else
                "Bearish"
            )
        
        # OI based PCR
        if put_oi is not None and call_oi is not None and call_oi > 0:
            oi_pcr = put_oi / call_oi
            result['oi_pcr'] = oi_pcr
            result['oi_pcr_interpretation'] = (
                "Bullish" if oi_pcr < 0.7 else
                "Neutral" if oi_pcr < 1.3 else
                "Bearish"
            )
        
        return result
    
    @staticmethod
    def sentiment_from_pcr(pcr: float) -> str:
        """Get market sentiment from PCR value."""
        if pcr < 0.5:
            return "Extremely Bullish"
        elif pcr < 0.7:
            return "Bullish"
        elif pcr < 1.0:
            return "Slightly Bullish"
        elif pcr < 1.3:
            return "Neutral"
        elif pcr < 1.5:
            return "Slightly Bearish"
        elif pcr < 2.0:
            return "Bearish"
        else:
            return "Extremely Bearish"


class VIXAnalyzer:
    """Analyze VIX and volatility metrics."""
    
    @staticmethod
    def interpret_vix_level(vix: float) -> Dict[str, str]:
        """
        Interpret VIX level.
        
        Args:
            vix: VIX value
        
        Returns:
            VIX interpretation
        """
        if vix < 12:
            level = "Very Low"
            market_state = "Low Volatility"
            implication = "Market is complacent, potential for volatility spike"
        elif vix < 16:
            level = "Low"
            market_state = "Calm"
            implication = "Normal market conditions, moderate trading opportunities"
        elif vix < 20:
            level = "Moderate"
            market_state = "Balanced"
            implication = "Standard volatility, good for most strategies"
        elif vix < 30:
            level = "High"
            market_state = "Nervous"
            implication = "Elevated volatility, increased option premiums"
        else:
            level = "Very High"
            market_state = "Panic/Crisis"
            implication = "Extreme volatility, potential market reversal ahead"
        
        return {
            'vix_level': vix,
            'vix_category': level,
            'market_state': market_state,
            'implication': implication,
        }
    
    @staticmethod
    def vix_percentile(current_vix: float, historical_vix: List[float]) -> Dict[str, any]:
        """
        Calculate VIX percentile from historical data.
        
        Args:
            current_vix: Current VIX value
            historical_vix: List of historical VIX values
        
        Returns:
            Percentile analysis
        """
        if not historical_vix:
            return {}
        
        sorted_vix = sorted(historical_vix)
        percentile = (sum(1 for v in sorted_vix if v <= current_vix) / len(sorted_vix)) * 100
        
        return {
            'current_vix': current_vix,
            'percentile': percentile,
            'historical_avg': np.mean(historical_vix),
            'historical_min': np.min(historical_vix),
            'historical_max': np.max(historical_vix),
            'vs_avg': "Above average" if current_vix > np.mean(historical_vix) else "Below average",
            'mean_reversion_potential': "Low" if 40 < percentile < 60 else "High",
        }
