"""Tests for pattern detection module."""
import pytest
from src.core.patterns import (
    infer_trend,
    detect_double_top,
    detect_double_bottom,
    _sma,
)
from src.data.models import Candle, MarketState


class TestSMA:
    """Test simple moving average calculation."""
    
    def test_sma_basic(self):
        """Test basic SMA calculation."""
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        assert _sma(values, 3) == 40.0  # (30 + 40 + 50) / 3
        
    def test_sma_window_larger_than_data(self):
        """Test SMA when window is larger than available data."""
        values = [10.0, 20.0]
        assert _sma(values, 5) == 15.0  # (10 + 20) / 2
        
    def test_sma_empty_list(self):
        """Test SMA with empty list."""
        assert _sma([], 5) == 0.0
        
    def test_sma_single_value(self):
        """Test SMA with single value."""
        assert _sma([42.0], 1) == 42.0


class TestInferTrend:
    """Test trend inference logic."""
    
    def test_bullish_trend(self):
        """Test bullish trend detection."""
        candles = [
            Candle("2024-01-01 09:00", 100, 102, 99, 101),
            Candle("2024-01-01 09:01", 101, 103, 100, 102),
            Candle("2024-01-01 09:02", 102, 104, 101, 103),
            Candle("2024-01-01 09:03", 103, 105, 102, 104),
            Candle("2024-01-01 09:04", 104, 106, 103, 105),
        ]
        assert infer_trend(candles, ma_window=3) == MarketState.BULLISH
        
    def test_bearish_trend(self):
        """Test bearish trend detection."""
        candles = [
            Candle("2024-01-01 09:00", 105, 106, 104, 105),
            Candle("2024-01-01 09:01", 104, 105, 103, 104),
            Candle("2024-01-01 09:02", 103, 104, 102, 103),
            Candle("2024-01-01 09:03", 102, 103, 101, 102),
            Candle("2024-01-01 09:04", 101, 102, 100, 101),
        ]
        assert infer_trend(candles, ma_window=3) == MarketState.BEARISH
        
    def test_range_trend(self):
        """Test range-bound market detection."""
        candles = [
            Candle("2024-01-01 09:00", 100, 102, 99, 100),
            Candle("2024-01-01 09:01", 100, 102, 99, 101),
            Candle("2024-01-01 09:02", 101, 102, 99, 100),
            Candle("2024-01-01 09:03", 100, 102, 99, 100),
        ]
        assert infer_trend(candles, ma_window=3) == MarketState.RANGE
        
    def test_empty_candles(self):
        """Test with empty candle list."""
        assert infer_trend([]) == MarketState.RANGE
        
    def test_single_candle(self):
        """Test with single candle."""
        candles = [Candle("2024-01-01 09:00", 100, 102, 99, 101)]
        # With single candle, net_up/down comparison will be with itself
        result = infer_trend(candles, ma_window=1)
        assert result in [MarketState.RANGE, MarketState.BULLISH, MarketState.BEARISH]


class TestDetectDoubleTop:
    """Test double-top pattern detection."""
    
    def test_valid_double_top(self):
        """Test detection of valid double-top pattern."""
        candles = [
            Candle("2024-01-01 09:00", 100, 105, 99, 104),   # First peak
            Candle("2024-01-01 09:01", 104, 105, 100, 101),  # Decline
            Candle("2024-01-01 09:02", 101, 102, 98, 99),    # Valley
            Candle("2024-01-01 09:03", 99, 103, 98, 102),    # Recovery
            Candle("2024-01-01 09:04", 102, 105.1, 101, 101),  # Second peak with rejection (close < open)
        ]
        is_pattern, idx, ref_high = detect_double_top(candles, lookback=8, tolerance_pct=0.002)
        assert is_pattern is True
        assert idx == 4  # Last candle index
        assert ref_high is not None
        
    def test_no_double_top_single_peak(self):
        """Test no pattern with single peak."""
        candles = [
            Candle("2024-01-01 09:00", 100, 102, 99, 101),
            Candle("2024-01-01 09:01", 101, 105, 100, 104),  # Single peak
            Candle("2024-01-01 09:02", 104, 105, 101, 102),  # No rejection
        ]
        is_pattern, _, _ = detect_double_top(candles, lookback=8, tolerance_pct=0.002)
        assert is_pattern is False
        
    def test_double_top_tolerance_exceeded(self):
        """Test when peaks are too far apart (tolerance exceeded)."""
        candles = [
            Candle("2024-01-01 09:00", 100, 105, 99, 104),   # First peak at 105
            Candle("2024-01-01 09:01", 104, 105, 100, 101),
            Candle("2024-01-01 09:02", 101, 102, 98, 99),
            Candle("2024-01-01 09:03", 99, 103, 98, 102),
            Candle("2024-01-01 09:04", 102, 108, 101, 103),  # Second peak at 108 (too far)
        ]
        is_pattern, _, _ = detect_double_top(candles, lookback=8, tolerance_pct=0.002)
        # Should fail because 108 vs 105 is > 0.2% tolerance
        assert is_pattern is False
        
    def test_double_top_no_rejection(self):
        """Test when there's no rejection candle."""
        candles = [
            Candle("2024-01-01 09:00", 100, 105, 99, 104),   # First peak
            Candle("2024-01-01 09:01", 104, 105, 100, 101),
            Candle("2024-01-01 09:02", 101, 102, 98, 99),
            Candle("2024-01-01 09:03", 99, 103, 98, 102),
            Candle("2024-01-01 09:04", 102, 105, 101, 105),  # Close above open (no rejection)
        ]
        is_pattern, _, _ = detect_double_top(candles, lookback=8, tolerance_pct=0.002)
        assert is_pattern is False
        
    def test_insufficient_candles(self):
        """Test with insufficient candles."""
        candles = [
            Candle("2024-01-01 09:00", 100, 105, 99, 104),
            Candle("2024-01-01 09:01", 104, 105, 100, 101),
        ]
        is_pattern, _, _ = detect_double_top(candles)
        assert is_pattern is False


class TestDetectDoubleBottom:
    """Test double-bottom pattern detection."""
    
    def test_valid_double_bottom(self):
        """Test detection of valid double-bottom pattern."""
        candles = [
            Candle("2024-01-01 09:00", 105, 106, 100, 101),  # First trough at low=100
            Candle("2024-01-01 09:01", 101, 104, 100, 103),  # Recovery
            Candle("2024-01-01 09:02", 103, 107, 102, 106),  # Peak
            Candle("2024-01-01 09:03", 106, 107, 99.9, 103),  # Second trough at low=99.9 (second_idx)
            Candle("2024-01-01 09:04", 99, 105, 99.9, 104),  # Rejection candle (open < close)
        ]
        is_pattern, idx, ref_low = detect_double_bottom(candles, lookback=8, tolerance_pct=0.002)
        assert is_pattern is True
        assert idx == 4
        assert ref_low is not None
        
    def test_no_double_bottom_single_trough(self):
        """Test no pattern with single trough."""
        candles = [
            Candle("2024-01-01 09:00", 105, 106, 104, 105),
            Candle("2024-01-01 09:01", 105, 106, 100, 101),  # Single trough
            Candle("2024-01-01 09:02", 101, 104, 100, 103),
        ]
        is_pattern, _, _ = detect_double_bottom(candles, lookback=8, tolerance_pct=0.002)
        assert is_pattern is False
        
    def test_double_bottom_tolerance_exceeded(self):
        """Test when troughs are too far apart."""
        candles = [
            Candle("2024-01-01 09:00", 105, 106, 100, 101),  # First trough at 100
            Candle("2024-01-01 09:01", 101, 104, 100, 103),
            Candle("2024-01-01 09:02", 103, 107, 102, 106),
            Candle("2024-01-01 09:03", 106, 107, 102, 103),
            Candle("2024-01-01 09:04", 103, 105, 95, 104),   # Second trough at 95 (too far)
        ]
        is_pattern, _, _ = detect_double_bottom(candles, lookback=8, tolerance_pct=0.002)
        assert is_pattern is False
        
    def test_double_bottom_no_rejection(self):
        """Test when there's no rejection candle."""
        candles = [
            Candle("2024-01-01 09:00", 105, 106, 100, 101),  # First trough
            Candle("2024-01-01 09:01", 101, 104, 100, 103),
            Candle("2024-01-01 09:02", 103, 107, 102, 106),
            Candle("2024-01-01 09:03", 106, 107, 102, 103),
            Candle("2024-01-01 09:04", 103, 105, 100, 101),  # Close below open (no rejection)
        ]
        is_pattern, _, _ = detect_double_bottom(candles, lookback=8, tolerance_pct=0.002)
        assert is_pattern is False
        
    def test_insufficient_candles(self):
        """Test with insufficient candles."""
        candles = [
            Candle("2024-01-01 09:00", 105, 106, 100, 101),
            Candle("2024-01-01 09:01", 101, 104, 100, 103),
        ]
        is_pattern, _, _ = detect_double_bottom(candles)
        assert is_pattern is False
