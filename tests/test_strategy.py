"""Tests for the non-directional strangle strategy."""
import pytest
from src.strategies.non_directional_strangle import NonDirectionalStrangleStrategy, Signal
from src.data.models import Candle, OIData, FuturesOI, MarketState


class TestNonDirectionalStrangleStrategy:
    """Test strategy signal generation."""
    
    def setup_method(self):
        """Set up strategy instance for tests."""
        self.strategy = NonDirectionalStrangleStrategy(
            tolerance_pct=0.002,
            min_oi_change_pct=0.0,
            fut_min_drop_pct=0.01
        )
    
    def test_empty_data(self):
        """Test with empty data."""
        signal = self.strategy.evaluate([], [], [])
        assert signal is None
        
    def test_insufficient_data(self):
        """Test with insufficient data (less than 4 candles)."""
        candles = [
            Candle("2024-01-01 09:00", 100, 102, 99, 101),
            Candle("2024-01-01 09:01", 101, 103, 100, 102),
        ]
        oi_data = [
            OIData("2024-01-01 09:00", oi_call_atm=1000, oi_put_atm=800),
            OIData("2024-01-01 09:01", oi_call_atm=1000, oi_put_atm=800),
        ]
        futures_data = [
            FuturesOI("2024-01-01 09:00", current_month_oi=5000, next_month_oi=3000),
            FuturesOI("2024-01-01 09:01", current_month_oi=5000, next_month_oi=3000),
        ]
        
        signal = self.strategy.evaluate(candles, oi_data, futures_data)
        # Pattern detection requires at least 4 candles, so should return None
        assert signal is None
        
    def test_range_market_no_signal(self):
        """Test that ranging market produces no signals."""
        # Range-bound candles - oscillating without clear trend
        candles = [
            Candle("2024-01-01 09:00", 100, 102, 99, 100),
            Candle("2024-01-01 09:01", 100, 102, 99, 101),
            Candle("2024-01-01 09:02", 101, 102, 99, 100),
            Candle("2024-01-01 09:03", 100, 102, 99, 100),
            Candle("2024-01-01 09:04", 100, 102, 99, 101),
        ]
        
        oi_data = [
            OIData(f"2024-01-01 09:0{i}", oi_call_atm=1000, oi_put_atm=800)
            for i in range(5)
        ]
        
        futures_data = [
            FuturesOI(f"2024-01-01 09:0{i}", current_month_oi=5000, next_month_oi=3000)
            for i in range(5)
        ]
        
        signal = self.strategy.evaluate(candles, oi_data, futures_data)
        # Range market should not trigger signals
        assert signal is None
        
    def test_signal_structure_when_generated(self):
        """Test that signals have correct structure when generated."""
        # Create a scenario that might generate a signal
        # Using simple uptrending candles
        candles = [
            Candle("2024-01-01 09:00", 100, 102, 99, 101),
            Candle("2024-01-01 09:01", 101, 103, 100, 102),
            Candle("2024-01-01 09:02", 102, 104, 101, 103),
            Candle("2024-01-01 09:03", 103, 105, 102, 104),
            Candle("2024-01-01 09:04", 104, 106, 103, 105),
        ]
        
        oi_data = [
            OIData(f"2024-01-01 09:0{i}", oi_call_atm=1000, oi_put_atm=800)
            for i in range(5)
        ]
        
        futures_data = [
            FuturesOI(f"2024-01-01 09:0{i}", current_month_oi=5000, next_month_oi=3000)
            for i in range(5)
        ]
        
        signal = self.strategy.evaluate(candles, oi_data, futures_data)
        
        # Signal may or may not be generated depending on pattern detection
        # If generated, verify structure
        if signal is not None:
            assert hasattr(signal, 'timestamp')
            assert hasattr(signal, 'action')
            assert hasattr(signal, 'context')
            assert signal.action in ['no_trade', 'sell_iron_condor']
            assert isinstance(signal.context, dict)
            
    def test_strategy_parameters(self):
        """Test that strategy accepts and stores parameters correctly."""
        strat = NonDirectionalStrangleStrategy(
            tolerance_pct=0.003,
            min_oi_change_pct=0.01,
            fut_min_drop_pct=0.02
        )
        
        assert strat.tolerance_pct == 0.003
        assert strat.min_oi_change_pct == 0.01
        assert strat.fut_min_drop_pct == 0.02
        
    def test_no_pattern_detected(self):
        """Test when no pattern is detected in trending market."""
        # Smooth uptrend without double-top pattern
        candles = [
            Candle("2024-01-01 09:00", 100, 102, 99, 101),
            Candle("2024-01-01 09:01", 101, 103, 100, 102),
            Candle("2024-01-01 09:02", 102, 104, 101, 103),
            Candle("2024-01-01 09:03", 103, 105, 102, 104),
        ]
        
        oi_data = [
            OIData(f"2024-01-01 09:0{i}", oi_call_atm=1000, oi_put_atm=800)
            for i in range(4)
        ]
        
        futures_data = [
            FuturesOI(f"2024-01-01 09:0{i}", current_month_oi=5000, next_month_oi=3000)
            for i in range(4)
        ]
        
        signal = self.strategy.evaluate(candles, oi_data, futures_data)
        # No clear double-top/bottom pattern, should return None
        assert signal is None
