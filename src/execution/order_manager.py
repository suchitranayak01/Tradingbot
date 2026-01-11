import logging
from typing import Optional, Dict, List
from datetime import datetime
import math

from src.brokers.angelone import AngelOneClient
from src.strategies.non_directional_strangle import Signal

logger = logging.getLogger(__name__)


class OrderManager:
    """Manages order execution based on strategy signals."""
    
    def __init__(
        self,
        broker: AngelOneClient,
        underlying_symbol: str,
        exchange: str,
        lot_size: int,
        max_loss_per_trade: float,
        dry_run: bool = True,
    ):
        self.broker = broker
        self.underlying_symbol = underlying_symbol
        self.exchange = exchange
        self.lot_size = lot_size
        self.max_loss_per_trade = max_loss_per_trade
        self.dry_run = dry_run
        self.active_positions: List[Dict] = []
        
    def execute_signal(self, signal: Signal, current_price: float) -> bool:
        """Execute orders based on strategy signal.
        
        For a strangle:
        - Sell OTM Call at (current_price + call_distance)
        - Sell OTM Put at (current_price - put_distance)
        """
        if signal.action == "no_trade":
            logger.info(f"Signal is no_trade: {signal.context.get('reason')}")
            return False
        
        if signal.action != "sell_strangle":
            logger.warning(f"Unknown signal action: {signal.action}")
            return False
        
        # Calculate strikes
        call_strike = self._round_to_strike(current_price + (signal.call_distance or 100))
        put_strike = self._round_to_strike(current_price - (signal.put_distance or 100))
        
        logger.info(f"Executing strangle: Sell {call_strike} CE, Sell {put_strike} PE")
        
        if self.dry_run:
            logger.info("[DRY RUN] Would place orders:")
            logger.info(f"  - SELL {self.lot_size} x {self.underlying_symbol} {call_strike} CE")
            logger.info(f"  - SELL {self.lot_size} x {self.underlying_symbol} {put_strike} PE")
            return True
        
        # Get option symbols and tokens (simplified - you need actual mapping)
        call_symbol, call_token = self._get_option_symbol(call_strike, "CE", signal.timestamp)
        put_symbol, put_token = self._get_option_symbol(put_strike, "PE", signal.timestamp)
        
        if not call_symbol or not put_symbol:
            logger.error("Failed to resolve option symbols")
            return False
        
        # Place call sell order
        call_order_id = self.broker.place_order(
            symbol=call_symbol,
            token=call_token,
            exchange=self.exchange,
            transaction_type="SELL",
            quantity=self.lot_size,
            order_type="MARKET",
            product_type="CARRYFORWARD",
        )
        
        # Place put sell order
        put_order_id = self.broker.place_order(
            symbol=put_symbol,
            token=put_token,
            exchange=self.exchange,
            transaction_type="SELL",
            quantity=self.lot_size,
            order_type="MARKET",
            product_type="CARRYFORWARD",
        )
        
        if call_order_id and put_order_id:
            self.active_positions.append({
                "timestamp": signal.timestamp,
                "call_order": call_order_id,
                "put_order": put_order_id,
                "call_strike": call_strike,
                "put_strike": put_strike,
            })
            logger.info(f"Strangle executed: Call={call_order_id}, Put={put_order_id}")
            return True
        else:
            logger.error("Failed to execute complete strangle")
            return False
    
    def _round_to_strike(self, price: float, step: int = 50) -> int:
        """Round price to nearest strike interval (e.g., 50 for NIFTY)."""
        return int(round(price / step) * step)
    
    def _get_option_symbol(
        self,
        strike: int,
        option_type: str,
        timestamp: str,
    ) -> tuple[Optional[str], Optional[str]]:
        """Build option symbol for Angel One.
        
        Format: NIFTY26JAN23500CE (for NIFTY)
        Returns (symbol, token) tuple.
        
        NOTE: This is simplified. You should use searchScrip API
        or maintain a symbol master file for accurate token mapping.
        """
        try:
            # Parse timestamp to get expiry (next Thursday for weekly NIFTY)
            dt = datetime.strptime(timestamp.split()[0], "%Y-%m-%d")
            # Simplified: assume current month expiry (need proper expiry calculation)
            expiry_str = dt.strftime("%y%b").upper()  # e.g., 26JAN
            
            symbol = f"{self.underlying_symbol}{expiry_str}{strike}{option_type}"
            
            # TODO: Use broker.client.searchScrip to get actual token
            # For now, returning None token as placeholder
            logger.warning(f"Symbol resolution needed for: {symbol}")
            return symbol, "0"  # Placeholder token
            
        except Exception as e:
            logger.error(f"Error building option symbol: {e}")
            return None, None
    
    def get_positions_summary(self) -> Dict:
        """Get summary of active positions."""
        if self.dry_run:
            return {"mode": "dry_run", "positions": self.active_positions}
        
        positions = self.broker.get_positions()
        return positions or {}
