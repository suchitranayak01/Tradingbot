"""Database manager for trading bot persistence."""
import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, db_path: str = "data/trading_bot.db"):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: Optional[sqlite3.Connection] = None
        self._initialize_database()
        
    def _initialize_database(self) -> None:
        """Initialize database schema if it doesn't exist."""
        schema_path = Path(__file__).parent / "schema.sql"
        
        if not schema_path.exists():
            logger.error(f"Schema file not found: {schema_path}")
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
            
        with self.get_connection() as conn:
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
                conn.executescript(schema_sql)
                conn.commit()
                
        logger.info(f"Database initialized: {self.db_path}")
        
    @contextmanager
    def get_connection(self):
        """
        Get database connection as context manager.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()
            
    def save_signal(
        self,
        timestamp: str,
        action: str,
        situation: str,
        reason: str,
        call_distance: Optional[int] = None,
        put_distance: Optional[int] = None,
        hedge_distance: Optional[int] = None,
        current_price: Optional[float] = None
    ) -> int:
        """
        Save trading signal to database.
        
        Args:
            timestamp: Signal timestamp
            action: Signal action
            situation: Strategy situation (1, 2, 3, etc.)
            reason: Reason for signal
            call_distance: Call strike distance
            put_distance: Put strike distance
            hedge_distance: Hedge strike distance
            current_price: Current underlying price
            
        Returns:
            Signal ID
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO signals (
                    timestamp, action, situation, reason,
                    call_distance, put_distance, hedge_distance, current_price
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp, action, situation, reason,
                call_distance, put_distance, hedge_distance, current_price
            ))
            conn.commit()
            signal_id = cursor.lastrowid
            
        logger.info(f"Saved signal {signal_id}: {action} at {timestamp}")
        return signal_id
        
    def save_order(
        self,
        signal_id: int,
        order_id: str,
        symbol: str,
        strike: int,
        option_type: str,
        side: str,
        quantity: int,
        order_type: str,
        product_type: str,
        status: str,
        price: Optional[float] = None
    ) -> int:
        """
        Save order to database.
        
        Args:
            signal_id: Related signal ID
            order_id: Broker's order ID
            symbol: Option symbol
            strike: Strike price
            option_type: 'CE' or 'PE'
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            order_type: Order type ('MARKET', 'LIMIT')
            product_type: Product type ('INTRADAY', 'CARRYFORWARD')
            status: Order status
            price: Order price (for limit orders)
            
        Returns:
            Order record ID
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO orders (
                    signal_id, order_id, symbol, strike, option_type,
                    side, quantity, order_type, product_type, status, price
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal_id, order_id, symbol, strike, option_type,
                side, quantity, order_type, product_type, status, price
            ))
            conn.commit()
            
        logger.info(f"Saved order {order_id}: {side} {quantity} {symbol}")
        return cursor.lastrowid
        
    def update_order_status(
        self,
        order_id: str,
        status: str,
        average_price: Optional[float] = None,
        filled_quantity: Optional[int] = None,
        rejection_reason: Optional[str] = None
    ) -> None:
        """
        Update order status.
        
        Args:
            order_id: Broker's order ID
            status: New status
            average_price: Average execution price
            filled_quantity: Filled quantity
            rejection_reason: Rejection reason if rejected
        """
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE orders SET
                    status = ?,
                    average_price = COALESCE(?, average_price),
                    filled_quantity = COALESCE(?, filled_quantity),
                    rejection_reason = COALESCE(?, rejection_reason),
                    updated_at = CURRENT_TIMESTAMP
                WHERE order_id = ?
            """, (status, average_price, filled_quantity, rejection_reason, order_id))
            conn.commit()
            
        logger.info(f"Updated order {order_id}: status={status}")
        
    def get_recent_signals(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent signals.
        
        Args:
            limit: Maximum number of signals to retrieve
            
        Returns:
            List of signal dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM signals
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
            
    def get_open_orders(self) -> List[Dict[str, Any]]:
        """
        Get all open (pending) orders.
        
        Returns:
            List of order dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM orders
                WHERE status IN ('PENDING', 'OPEN')
                ORDER BY placed_at DESC
            """)
            
            return [dict(row) for row in cursor.fetchall()]
            
    def save_system_state(self, key: str, value: str) -> None:
        """
        Save or update system state.
        
        Args:
            key: State key
            value: State value (JSON string)
        """
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO system_state (state_key, state_value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value))
            conn.commit()
            
        logger.debug(f"Saved system state: {key}")
        
    def get_system_state(self, key: str) -> Optional[str]:
        """
        Get system state value.
        
        Args:
            key: State key
            
        Returns:
            State value or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT state_value FROM system_state WHERE state_key = ?
            """, (key,))
            
            row = cursor.fetchone()
            return row['state_value'] if row else None
            
    def get_daily_pnl(self, date: str) -> Optional[Dict[str, Any]]:
        """
        Get daily P&L metrics.
        
        Args:
            date: Date in 'YYYY-MM-DD' format
            
        Returns:
            Daily metrics dictionary or None
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM daily_metrics WHERE date = ?
            """, (date,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
            
    def cleanup_old_data(self, days: int = 30) -> None:
        """
        Cleanup old data to prevent database bloat.
        
        Args:
            days: Keep data newer than this many days
        """
        cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_str = cutoff_date.isoformat()
        
        with self.get_connection() as conn:
            # Don't delete completed trades for analytics
            # Only cleanup intermediate data
            cursor = conn.execute("""
                DELETE FROM system_state
                WHERE updated_at < datetime('now', ?)
            """, (f'-{days} days',))
            
            deleted = cursor.rowcount
            conn.commit()
            
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old records (older than {days} days)")
