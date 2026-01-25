"""Tests for order manager."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from src.execution.order_manager import OrderManager
from src.strategies.non_directional_strangle import Signal


class TestOrderManager:
    """Test order manager functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_broker = Mock()
        self.order_manager = OrderManager(
            broker=self.mock_broker,
            underlying_symbol="NIFTY",
            exchange="NFO",
            lot_size=50,
            max_loss_per_trade=5000,
            capital=1000000,
            dry_run=True
        )
    
    def test_round_to_strike_basic(self):
        """Test strike rounding to nearest 50."""
        assert self.order_manager._round_to_strike(19523.45) == 19500  # Rounds down
        assert self.order_manager._round_to_strike(19525.00) == 19500  # Midpoint rounds down in Python3
        assert self.order_manager._round_to_strike(19512.00) == 19500
        assert self.order_manager._round_to_strike(19538.00) == 19550  # This should round up
        
    def test_round_to_strike_exact(self):
        """Test rounding when already at strike."""
        assert self.order_manager._round_to_strike(19500.0) == 19500
        assert self.order_manager._round_to_strike(20000.0) == 20000
        
    def test_execute_no_trade_signal(self):
        """Test that no_trade signals don't execute."""
        signal = Signal(
            timestamp="2024-01-01 09:00",
            action="no_trade",
            context={"reason": "Test no trade"},
        )
        
        result = self.order_manager.execute_signal(signal, 19500)
        assert result is False
        
    def test_execute_invalid_signal(self):
        """Test handling of invalid signal action."""
        signal = Signal(
            timestamp="2024-01-01 09:00",
            action="invalid_action",
            context={},
        )
        
        result = self.order_manager.execute_signal(signal, 19500)
        assert result is False
        
    def test_dry_run_execution(self):
        """Test dry run mode logs but doesn't place orders."""
        signal = Signal(
            timestamp="2024-01-01 09:00",
            action="sell_iron_condor",
            context={"reason": "Test signal"},
            call_distance=100,
            put_distance=100,
            hedge_distance=900,
        )
        
        result = self.order_manager.execute_signal(signal, 19500)
        
        # Should return True in dry run
        assert result is True
        # Should not call broker
        self.mock_broker.place_order.assert_not_called()
        
    def test_strike_calculation_symmetric(self):
        """Test strike calculation for symmetric strangle."""
        signal = Signal(
            timestamp="2024-01-01 09:00",
            action="sell_iron_condor",
            context={"reason": "Situation 2"},
            call_distance=100,
            put_distance=100,
            hedge_distance=900,
        )
        
        current_price = 19500
        
        # In dry run, we can check the logged strikes
        with patch('src.execution.order_manager.logger') as mock_logger:
            self.order_manager.execute_signal(signal, current_price)
            
            # Verify info calls were made (logging the strikes)
            assert mock_logger.info.called
            
        # Expected strikes:
        # buy_call_strike = 19500 + 900 = 20400
        # sell_call_strike = 19500 + 100 = 19600
        # buy_put_strike = 19500 - 900 = 18600
        # sell_put_strike = 19500 - 100 = 19400
        
    def test_strike_calculation_asymmetric(self):
        """Test strike calculation for asymmetric strangle."""
        signal = Signal(
            timestamp="2024-01-01 09:00",
            action="sell_iron_condor",
            context={"reason": "Situation 3"},
            call_distance=75,
            put_distance=125,
            hedge_distance=900,
        )
        
        current_price = 20000
        
        with patch('src.execution.order_manager.logger') as mock_logger:
            result = self.order_manager.execute_signal(signal, current_price)
            assert result is True
            
        # Expected strikes:
        # buy_call_strike = 20000 + 900 = 20900
        # sell_call_strike = 20000 + 75 = 20075 -> rounds to 20100
        # buy_put_strike = 20000 - 900 = 19100
        # sell_put_strike = 20000 - 125 = 19875 -> rounds to 19900
        
    def test_sl_calculation(self):
        """Test stop loss calculation as 1% of capital."""
        signal = Signal(
            timestamp="2024-01-01 09:00",
            action="sell_iron_condor",
            context={},
            call_distance=100,
            put_distance=100,
            hedge_distance=900,
        )
        
        # Capital is 1,000,000, so SL should be 10,000
        expected_sl = 1000000 * 0.01
        
        with patch('src.execution.order_manager.logger') as mock_logger:
            self.order_manager.execute_signal(signal, 19500)
            
            # Check if SL was logged correctly
            info_calls = [str(call) for call in mock_logger.info.call_args_list]
            sl_logged = any(f"₹{expected_sl:,.0f}" in str(call) for call in info_calls)
            assert sl_logged
            
    def test_live_execution_success(self):
        """Test successful live order execution."""
        # Set up non-dry-run order manager
        self.order_manager.dry_run = False
        
        # Mock broker responses
        self.mock_broker.place_order.side_effect = ["ORDER1", "ORDER2", "ORDER3", "ORDER4"]
        
        # Mock symbol resolution
        self.order_manager._get_option_symbol = Mock(
            side_effect=[
                ("NIFTY24JAN20400CE", "12345"),  # buy call
                ("NIFTY24JAN19600CE", "12346"),  # sell call
                ("NIFTY24JAN18600PE", "12347"),  # buy put
                ("NIFTY24JAN19400PE", "12348"),  # sell put
            ]
        )
        
        signal = Signal(
            timestamp="2024-01-01 09:00",
            action="sell_iron_condor",
            context={},
            call_distance=100,
            put_distance=100,
            hedge_distance=900,
        )
        
        result = self.order_manager.execute_signal(signal, 19500)
        
        assert result is True
        assert self.mock_broker.place_order.call_count == 4
        assert len(self.order_manager.active_positions) == 1
        
    def test_live_execution_partial_failure(self):
        """Test handling of partial order execution failure."""
        self.order_manager.dry_run = False
        
        # First order succeeds, second fails
        self.mock_broker.place_order.side_effect = ["ORDER1", None, "ORDER3", "ORDER4"]
        
        self.order_manager._get_option_symbol = Mock(
            side_effect=[
                ("NIFTY24JAN20400CE", "12345"),
                ("NIFTY24JAN19600CE", "12346"),
                ("NIFTY24JAN18600PE", "12347"),
                ("NIFTY24JAN19400PE", "12348"),
            ]
        )
        
        signal = Signal(
            timestamp="2024-01-01 09:00",
            action="sell_iron_condor",
            context={},
            call_distance=100,
            put_distance=100,
            hedge_distance=900,
        )
        
        result = self.order_manager.execute_signal(signal, 19500)
        
        # Should fail if any order fails
        assert result is False
        
    def test_symbol_resolution_failure(self):
        """Test handling of symbol resolution failure."""
        self.order_manager.dry_run = False
        
        # Mock symbol resolution to return None
        self.order_manager._get_option_symbol = Mock(return_value=(None, None))
        
        signal = Signal(
            timestamp="2024-01-01 09:00",
            action="sell_iron_condor",
            context={},
            call_distance=100,
            put_distance=100,
            hedge_distance=900,
        )
        
        result = self.order_manager.execute_signal(signal, 19500)
        
        assert result is False
        
    def test_get_positions_summary_dry_run(self):
        """Test positions summary in dry run mode."""
        summary = self.order_manager.get_positions_summary()
        
        assert summary["mode"] == "dry_run"
        assert "positions" in summary
        
    def test_get_positions_summary_live(self):
        """Test positions summary in live mode."""
        self.order_manager.dry_run = False
        self.mock_broker.get_positions.return_value = {"positions": []}
        
        summary = self.order_manager.get_positions_summary()
        
        self.mock_broker.get_positions.assert_called_once()
        
    def test_capital_default(self):
        """Test default capital value."""
        om = OrderManager(
            broker=self.mock_broker,
            underlying_symbol="NIFTY",
            exchange="NFO",
            lot_size=50,
            max_loss_per_trade=5000,
        )
        
        assert om.capital == 1000000  # Default 10 lakhs
        
    def test_custom_capital(self):
        """Test custom capital value."""
        om = OrderManager(
            broker=self.mock_broker,
            underlying_symbol="NIFTY",
            exchange="NFO",
            lot_size=50,
            max_loss_per_trade=5000,
            capital=500000,
        )
        
        assert om.capital == 500000
