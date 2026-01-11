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
        capital: float = 1000000,  # Total trading capital
        dry_run: bool = True,
    ):
        self.broker = broker
        self.underlying_symbol = underlying_symbol
        self.exchange = exchange
        self.lot_size = lot_size
        self.max_loss_per_trade = max_loss_per_trade
        self.capital = capital  # Total capital for SL calculation
        self.dry_run = dry_run
        self.active_positions: List[Dict] = []
        
    def execute_signal(self, signal: Signal, current_price: float) -> bool:
        """Execute orders based on strategy signal.
        
        For Iron Condor (Buy Far, Sell Near):
        - BUY Call at (current_price + hedge_distance)  [900 points away - protection]
        - SELL Call at (current_price + call_distance)  [closer - profit taking]
        - BUY Put at (current_price - hedge_distance)   [900 points away - protection]
        - SELL Put at (current_price - put_distance)    [closer - profit taking]
        
        SL is capped at 1% of total capital deployed.
        """
        if signal.action == "no_trade":
            logger.info(f"Signal is no_trade: {signal.context.get('reason')}")
            return False
        
        if signal.action != "sell_iron_condor":
            logger.warning(f"Unknown signal action: {signal.action}")
            return False
        
        # Calculate strikes - BUY FAR (900 points), SELL NEAR (call_distance/put_distance)
        buy_call_strike = self._round_to_strike(current_price + signal.hedge_distance)
        sell_call_strike = self._round_to_strike(current_price + (signal.call_distance or 100))
        buy_put_strike = self._round_to_strike(current_price - signal.hedge_distance)
        sell_put_strike = self._round_to_strike(current_price - (signal.put_distance or 100))
        
        # Calculate SL as 1% of capital
        sl_amount = self.capital * 0.01
        
        logger.info(f"Executing Iron Condor (Buy Far, Sell Near):")
        logger.info(f"  BUY  Call {buy_call_strike} CE (900 points away), SELL Call {sell_call_strike} CE (closer)")
        logger.info(f"  BUY  Put  {buy_put_strike} PE (900 points away), SELL Put {sell_put_strike} PE (closer)")
        logger.info(f"  Capital: ₹{self.capital:,.0f}")
        logger.info(f"  Stop Loss (1% of capital): ₹{sl_amount:,.0f}")
        
        if self.dry_run:
            logger.info("[DRY RUN] Would place orders in sequence:")
            logger.info(f"  1. BUY  {self.lot_size} x {self.underlying_symbol} {buy_call_strike} CE")
            logger.info(f"  2. SELL {self.lot_size} x {self.underlying_symbol} {sell_call_strike} CE")
            logger.info(f"  3. BUY  {self.lot_size} x {self.underlying_symbol} {buy_put_strike} PE")
            logger.info(f"  4. SELL {self.lot_size} x {self.underlying_symbol} {sell_put_strike} PE")
            logger.info(f"  Stop Loss: ₹{sl_amount:,.0f}")
            return True
        
        # Get option symbols and tokens
        buy_call_symbol, buy_call_token = self._get_option_symbol(buy_call_strike, "CE", signal.timestamp)
        sell_call_symbol, sell_call_token = self._get_option_symbol(sell_call_strike, "CE", signal.timestamp)
        buy_put_symbol, buy_put_token = self._get_option_symbol(buy_put_strike, "PE", signal.timestamp)
        sell_put_symbol, sell_put_token = self._get_option_symbol(sell_put_strike, "PE", signal.timestamp)
        
        if not all([buy_call_symbol, sell_call_symbol, buy_put_symbol, sell_put_symbol]):
            logger.error("Failed to resolve option symbols")
            return False
        
        # PLACE BUY ORDERS FIRST
        buy_call_id = self.broker.place_order(
            symbol=buy_call_symbol, token=buy_call_token, exchange=self.exchange,
            transaction_type="BUY", quantity=self.lot_size, order_type="MARKET", product_type="CARRYFORWARD"
        )
        
        buy_put_id = self.broker.place_order(
            symbol=buy_put_symbol, token=buy_put_token, exchange=self.exchange,
            transaction_type="BUY", quantity=self.lot_size, order_type="MARKET", product_type="CARRYFORWARD"
        )
        
        # THEN PLACE SELL ORDERS
        sell_call_id = self.broker.place_order(
            symbol=sell_call_symbol, token=sell_call_token, exchange=self.exchange,
            transaction_type="SELL", quantity=self.lot_size, order_type="MARKET", product_type="CARRYFORWARD"
        )
        
        sell_put_id = self.broker.place_order(
            symbol=sell_put_symbol, token=sell_put_token, exchange=self.exchange,
            transaction_type="SELL", quantity=self.lot_size, order_type="MARKET", product_type="CARRYFORWARD"
        )
        
        if all([buy_call_id, sell_call_id, buy_put_id, sell_put_id]):
            self.active_positions.append({
                "timestamp": signal.timestamp,
                "type": "calendar_spread",
                "buy_call_order": buy_call_id,
                "sell_call_order": sell_call_id,
                "buy_put_order": buy_put_id,
                "sell_put_order": sell_put_id,
                "buy_call_strike": buy_call_strike,
                "sell_call_strike": sell_call_strike,
                "buy_put_strike": buy_put_strike,
                "sell_put_strike": sell_put_strike,
                "stop_loss": sl_amount,
                "capital_deployed": self.capital,
            })
            logger.info(f"Calendar Spread executed: BC={buy_call_id}, SC={sell_call_id}, BP={buy_put_id}, SP={sell_put_id}")
            logger.info(f"SL: ₹{sl_amount:,.0f}")
            return True
        else:
            logger.error("Failed to execute complete Calendar Spread")
            return False
        
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
            product_type=self.product_type,
        )
        
        # Place put sell order
        put_order_id = self.broker.place_order(
            symbol=put_symbol,
            token=put_token,
            exchange=self.exchange,
            transaction_type="SELL",
            quantity=self.lot_size,
            order_type="MARKET",
            product_type=self.product_type,
        )
        
        hedge_call_order_id = None
        hedge_put_order_id = None
        if call_order_id and put_order_id:
            if self.enable_hedge and self.hedge_distance > 0 and not self.dry_run:
                h_call_strike = call_strike + self.hedge_distance
                h_put_strike = put_strike - self.hedge_distance
                h_call_symbol, h_call_token = self._get_option_symbol(h_call_strike, "CE", signal.timestamp)
                h_put_symbol, h_put_token = self._get_option_symbol(h_put_strike, "PE", signal.timestamp)
                if h_call_symbol and h_put_symbol:
                    hedge_call_order_id = self.broker.place_order(
                        symbol=h_call_symbol,
                        token=h_call_token,
                        exchange=self.exchange,
                        transaction_type="BUY",
                        quantity=self.lot_size,
                        order_type="MARKET",
                        product_type=self.product_type,
                    )
                    hedge_put_order_id = self.broker.place_order(
                        symbol=h_put_symbol,
                        token=h_put_token,
                        exchange=self.exchange,
                        transaction_type="BUY",
                        quantity=self.lot_size,
                        order_type="MARKET",
                        product_type=self.product_type,
                    )
            self.active_positions.append({
                "timestamp": signal.timestamp,
                "call_order": call_order_id,
                "put_order": put_order_id,
                "call_strike": call_strike,
                "put_strike": put_strike,
                "hedge_call_order": hedge_call_order_id,
                "hedge_put_order": hedge_put_order_id,
            })
            logger.info(f"Strangle executed: Call={call_order_id}, Put={put_order_id}")
            if hedge_call_order_id and hedge_put_order_id:
                logger.info(f"Hedges executed: Call={hedge_call_order_id}, Put={hedge_put_order_id}")
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
        """Resolve option symbol and token via broker search."""
        try:
            dt = datetime.strptime(timestamp.split()[0], "%Y-%m-%d")
            expiry_str = dt.strftime("%y%b").upper()
            target = f"{self.underlying_symbol}{expiry_str}{strike}{option_type}"
            if self.dry_run:
                return target, "0"
            results = self.broker.search_scrip(self.exchange, target) if hasattr(self.broker, "search_scrip") else None
            if not results:
                logger.warning(f"Symbol search returned no results for: {target}")
                return target, "0"
            # Try exact match first
            for r in results:
                ts = r.get("tradingsymbol") or r.get("tradingSymbol") or r.get("symbol") or ""
                token = r.get("symboltoken") or r.get("token") or r.get("symbolToken") or r.get("instrument_token")
                if ts.upper() == target.upper():
                    return ts, str(token) if token is not None else None
            # Fallback: approximate match by strike and option type
            for r in results:
                ts = (r.get("tradingsymbol") or r.get("tradingSymbol") or r.get("symbol") or "").upper()
                token = r.get("symboltoken") or r.get("token") or r.get("symbolToken") or r.get("instrument_token")
                if str(strike) in ts and option_type in ts and self.underlying_symbol in ts:
                    return ts, str(token) if token is not None else None
            logger.warning(f"No matching scrip for: {target}")
            return target, "0"
        except Exception as e:
            logger.error(f"Error resolving option symbol: {e}")
            return None, None
    
    def get_positions_summary(self) -> Dict:
        """Get summary of active positions."""
        if self.dry_run:
            return {"mode": "dry_run", "positions": self.active_positions}
        
        positions = self.broker.get_positions()
        return positions or {}
