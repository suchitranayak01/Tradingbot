"""Tests for Open Interest (OI) analysis module."""
import pytest
from src.core.oi_analysis import (
    atm_call_oi_rising,
    atm_put_oi_rising,
    combined_futures_oi_change,
)
from src.data.models import OIData, FuturesOI


class TestATMCallOIRising:
    """Test ATM call OI rising detection."""
    
    def test_call_oi_rising(self):
        """Test detection of rising call OI."""
        oi_data = [
            OIData("2024-01-01 09:00", oi_call_atm=1000, oi_put_atm=800),
            OIData("2024-01-01 09:01", oi_call_atm=1100, oi_put_atm=850),
        ]
        assert atm_call_oi_rising(oi_data, min_pct=0.0) is True
        
    def test_call_oi_falling(self):
        """Test detection when call OI is falling."""
        oi_data = [
            OIData("2024-01-01 09:00", oi_call_atm=1100, oi_put_atm=800),
            OIData("2024-01-01 09:01", oi_call_atm=1000, oi_put_atm=850),
        ]
        assert atm_call_oi_rising(oi_data, min_pct=0.0) is False
        
    def test_call_oi_rising_with_threshold(self):
        """Test rising detection with percentage threshold."""
        oi_data = [
            OIData("2024-01-01 09:00", oi_call_atm=1000, oi_put_atm=800),
            OIData("2024-01-01 09:01", oi_call_atm=1050, oi_put_atm=850),  # 5% rise
        ]
        # Should pass with 4% threshold
        assert atm_call_oi_rising(oi_data, min_pct=0.04) is True
        # Should fail with 6% threshold
        assert atm_call_oi_rising(oi_data, min_pct=0.06) is False
        
    def test_call_oi_from_zero(self):
        """Test when previous OI is zero."""
        oi_data = [
            OIData("2024-01-01 09:00", oi_call_atm=0, oi_put_atm=800),
            OIData("2024-01-01 09:01", oi_call_atm=100, oi_put_atm=850),
        ]
        assert atm_call_oi_rising(oi_data, min_pct=0.0) is True
        
    def test_insufficient_data(self):
        """Test with insufficient data points."""
        oi_data = [OIData("2024-01-01 09:00", oi_call_atm=1000, oi_put_atm=800)]
        assert atm_call_oi_rising(oi_data) is False
        
    def test_empty_data(self):
        """Test with empty data."""
        assert atm_call_oi_rising([]) is False


class TestATMPutOIRising:
    """Test ATM put OI rising detection."""
    
    def test_put_oi_rising(self):
        """Test detection of rising put OI."""
        oi_data = [
            OIData("2024-01-01 09:00", oi_call_atm=1000, oi_put_atm=800),
            OIData("2024-01-01 09:01", oi_call_atm=1000, oi_put_atm=900),
        ]
        assert atm_put_oi_rising(oi_data, min_pct=0.0) is True
        
    def test_put_oi_falling(self):
        """Test detection when put OI is falling."""
        oi_data = [
            OIData("2024-01-01 09:00", oi_call_atm=1000, oi_put_atm=900),
            OIData("2024-01-01 09:01", oi_call_atm=1000, oi_put_atm=800),
        ]
        assert atm_put_oi_rising(oi_data, min_pct=0.0) is False
        
    def test_put_oi_rising_with_threshold(self):
        """Test rising detection with percentage threshold."""
        oi_data = [
            OIData("2024-01-01 09:00", oi_call_atm=1000, oi_put_atm=1000),
            OIData("2024-01-01 09:01", oi_call_atm=1000, oi_put_atm=1030),  # 3% rise
        ]
        assert atm_put_oi_rising(oi_data, min_pct=0.02) is True
        assert atm_put_oi_rising(oi_data, min_pct=0.04) is False
        
    def test_put_oi_from_zero(self):
        """Test when previous put OI is zero."""
        oi_data = [
            OIData("2024-01-01 09:00", oi_call_atm=1000, oi_put_atm=0),
            OIData("2024-01-01 09:01", oi_call_atm=1000, oi_put_atm=100),
        ]
        assert atm_put_oi_rising(oi_data, min_pct=0.0) is True
        
    def test_insufficient_data(self):
        """Test with insufficient data points."""
        oi_data = [OIData("2024-01-01 09:00", oi_call_atm=1000, oi_put_atm=800)]
        assert atm_put_oi_rising(oi_data) is False


class TestCombinedFuturesOIChange:
    """Test futures OI change detection."""
    
    def test_futures_oi_dropping(self):
        """Test detection of dropping futures OI."""
        futures_data = [
            FuturesOI("2024-01-01 09:00", current_month_oi=5000, next_month_oi=3000),  # Combined: 8000
            FuturesOI("2024-01-01 09:01", current_month_oi=4800, next_month_oi=2800),  # Combined: 7600 (5% drop)
        ]
        is_dropping, had_rise = combined_futures_oi_change(futures_data, min_drop_pct=0.01)
        assert is_dropping is True
        
    def test_futures_oi_rising(self):
        """Test when futures OI is rising."""
        futures_data = [
            FuturesOI("2024-01-01 09:00", current_month_oi=5000, next_month_oi=3000),  # Combined: 8000
            FuturesOI("2024-01-01 09:01", current_month_oi=5200, next_month_oi=3200),  # Combined: 8400
        ]
        is_dropping, had_rise = combined_futures_oi_change(futures_data, min_drop_pct=0.01)
        assert is_dropping is False
        
    def test_recent_rise_detection(self):
        """Test detection of recent rise in futures OI."""
        futures_data = [
            FuturesOI("2024-01-01 09:00", current_month_oi=5000, next_month_oi=3000),  # 8000
            FuturesOI("2024-01-01 09:01", current_month_oi=5100, next_month_oi=3100),  # 8200 (2.5% rise)
            FuturesOI("2024-01-01 09:02", current_month_oi=5000, next_month_oi=3000),  # 8000 (drop)
            FuturesOI("2024-01-01 09:03", current_month_oi=4900, next_month_oi=2900),  # 7800
        ]
        is_dropping, had_rise = combined_futures_oi_change(
            futures_data, 
            min_drop_pct=0.01,
            recent_rise_window=4,
            min_recent_rise_pct=0.01
        )
        assert is_dropping is True  # Latest is dropping
        assert had_rise is True     # Had rise in recent window
        
    def test_no_recent_rise(self):
        """Test when there's no recent rise."""
        futures_data = [
            FuturesOI("2024-01-01 09:00", current_month_oi=5000, next_month_oi=3000),  # 8000
            FuturesOI("2024-01-01 09:01", current_month_oi=4900, next_month_oi=2900),  # 7800
            FuturesOI("2024-01-01 09:02", current_month_oi=4800, next_month_oi=2800),  # 7600
        ]
        is_dropping, had_rise = combined_futures_oi_change(
            futures_data,
            min_drop_pct=0.01,
            recent_rise_window=3,
            min_recent_rise_pct=0.01
        )
        assert is_dropping is True
        assert had_rise is False
        
    def test_drop_threshold(self):
        """Test drop threshold requirements."""
        futures_data = [
            FuturesOI("2024-01-01 09:00", current_month_oi=10000, next_month_oi=5000),  # 15000
            FuturesOI("2024-01-01 09:01", current_month_oi=9950, next_month_oi=4950),   # 14900 (0.67% drop)
        ]
        # Should pass with 0.5% threshold
        is_dropping, _ = combined_futures_oi_change(futures_data, min_drop_pct=0.005)
        assert is_dropping is True
        
        # Should fail with 1% threshold
        is_dropping, _ = combined_futures_oi_change(futures_data, min_drop_pct=0.01)
        assert is_dropping is False
        
    def test_insufficient_data(self):
        """Test with insufficient data."""
        futures_data = [FuturesOI("2024-01-01 09:00", current_month_oi=5000, next_month_oi=3000)]
        is_dropping, had_rise = combined_futures_oi_change(futures_data)
        assert is_dropping is False
        assert had_rise is False
        
    def test_empty_data(self):
        """Test with empty data."""
        is_dropping, had_rise = combined_futures_oi_change([])
        assert is_dropping is False
        assert had_rise is False
        
    def test_zero_previous_oi(self):
        """Test when previous combined OI is zero."""
        futures_data = [
            FuturesOI("2024-01-01 09:00", current_month_oi=0, next_month_oi=0),
            FuturesOI("2024-01-01 09:01", current_month_oi=5000, next_month_oi=3000),
        ]
        is_dropping, had_rise = combined_futures_oi_change(futures_data)
        assert is_dropping is False  # Can't calculate percentage with zero base
