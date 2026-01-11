import logging
from typing import Optional, Dict, Any
from datetime import datetime
import pyotp

try:
    from SmartApi.smartConnect import SmartConnect
except ImportError:
    # Fallback for different package structure
    from smartapi.smartConnect import SmartConnect

logger = logging.getLogger(__name__)


class AngelOneClient:
    """Angel One SmartAPI client wrapper for order execution and market data."""
    
    def __init__(
        self,
        api_key: str,
        client_id: str,
        password: str,
        totp_secret: Optional[str] = None,
    ):
        self.api_key = api_key
        self.client_id = client_id
        self.password = password
        self.totp_secret = totp_secret
        self.client: Optional[SmartConnect] = None
        self.session_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        
    def login(self) -> bool:
        """Login to Angel One and establish session."""
        try:
            self.client = SmartConnect(api_key=self.api_key)
            
            # Generate TOTP if secret is provided
            totp = None
            if self.totp_secret:
                totp = pyotp.TOTP(self.totp_secret).now()
            
            # Generate session
            data = self.client.generateSession(
                clientCode=self.client_id,
                password=self.password,
                totp=totp
            )
            
            if data['status']:
                self.session_token = data['data']['jwtToken']
                self.refresh_token = data['data']['refreshToken']
                logger.info(f"Login successful for client {self.client_id}")
                return True
            else:
                logger.error(f"Login failed: {data.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Login exception: {e}")
            return False
    
    def get_ltp(self, exchange: str, symbol: str, token: str) -> Optional[float]:
        """Get last traded price for a symbol."""
        try:
            data = self.client.ltpData(exchange, symbol, token)
            if data and data['status']:
                return float(data['data']['ltp'])
            return None
        except Exception as e:
            logger.error(f"Error fetching LTP for {symbol}: {e}")
            return None
    
    def get_option_chain(self, symbol: str, exchange: str = "NFO") -> Optional[Dict]:
        """Fetch option chain data (simplified)."""
        try:
            # Note: Angel One doesn't have direct option chain API
            # You may need to use searchScrip and build chain manually
            logger.warning("Option chain fetching requires manual symbol search")
            return None
        except Exception as e:
            logger.error(f"Error fetching option chain: {e}")
            return None
    
    def place_order(
        self,
        symbol: str,
        token: str,
        exchange: str,
        transaction_type: str,  # BUY or SELL
        quantity: int,
        order_type: str = "MARKET",
        product_type: str = "CARRYFORWARD",  # INTRADAY or CARRYFORWARD
        price: float = 0.0,
    ) -> Optional[str]:
        """Place an order on Angel One.
        
        Returns order_id if successful, None otherwise.
        """
        try:
            order_params = {
                "variety": "NORMAL",
                "tradingsymbol": symbol,
                "symboltoken": token,
                "transactiontype": transaction_type,
                "exchange": exchange,
                "ordertype": order_type,
                "producttype": product_type,
                "duration": "DAY",
                "price": str(price),
                "squareoff": "0",
                "stoploss": "0",
                "quantity": str(quantity)
            }
            
            response = self.client.placeOrder(order_params)
            
            if response and response.get('status'):
                order_id = response['data']['orderid']
                logger.info(f"Order placed successfully: {order_id} | {transaction_type} {quantity} x {symbol}")
                return order_id
            else:
                logger.error(f"Order placement failed: {response.get('message', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Order placement exception: {e}")
            return None
    
    def get_order_book(self) -> Optional[list]:
        """Fetch current order book."""
        try:
            response = self.client.orderBook()
            if response and response.get('status'):
                return response['data']
            return None
        except Exception as e:
            logger.error(f"Error fetching order book: {e}")
            return None
    
    def get_positions(self) -> Optional[Dict]:
        """Fetch current positions."""
        try:
            response = self.client.position()
            if response and response.get('status'):
                return response['data']
            return None
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return None
    
    def logout(self):
        """Logout from Angel One session."""
        try:
            if self.client:
                self.client.terminateSession(self.client_id)
                logger.info("Logged out successfully")
        except Exception as e:
            logger.error(f"Logout error: {e}")
