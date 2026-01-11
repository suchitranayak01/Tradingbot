import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class KotakNeoClient:
    """Kotak Securities Neo API client wrapper for order execution and market data."""
    
    def __init__(
        self,
        api_key: str,
        user_id: str,
        password: str,
        consumer_key: str,
        consumer_secret: str,
    ):
        self.api_key = api_key
        self.user_id = user_id
        self.password = password
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.client: Optional[Any] = None
        self.session_token: Optional[str] = None
        
    def login(self) -> bool:
        """Login to Kotak Neo and establish session."""
        try:
            # Lazy import KotakNeo to avoid import errors in dry-run environments
            KotakNeoAPI = None
            try:
                from neo_api_client import NeoAPI as KotakNeoAPI
            except ImportError:
                try:
                    from kotakneo import NeoAPI as KotakNeoAPI
                except ImportError:
                    logger.error("Kotak Neo API not installed. Please install neo-api-client package.")
                    return False

            # Initialize the client
            self.client = KotakNeoAPI(
                api_key=self.api_key,
                consumer_key=self.consumer_key,
                consumer_secret=self.consumer_secret,
                environment='live'  # Use 'uat' for testing
            )
            
            # Login with user credentials
            login_response = self.client.login(
                userid=self.user_id,
                password=self.password
            )
            
            if login_response and login_response.get('status') == 'success':
                self.session_token = login_response.get('data', {}).get('token')
                logger.info(f"Kotak Neo login successful for user {self.user_id}")
                return True
            else:
                error_msg = login_response.get('message', 'Unknown error') if isinstance(login_response, dict) else str(login_response)
                logger.error(f"Kotak Neo login failed: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"Kotak Neo login exception: {e}")
            return False

    def search_scrip(self, exchange: str, query: str) -> Optional[List[Dict]]:
        """Search scrips to resolve tokens and trading symbols."""
        try:
            if not self.client:
                logger.error("Client not initialized; call login() first")
                return None
            
            # Search instrument
            search_response = self.client.searchScrip(
                exch=exchange,
                instname='',
                symbol=query
            )
            
            if search_response and search_response.get('status') == 'success':
                return search_response.get('data', [])
            
            logger.error(f"searchScrip failed: {search_response.get('message', 'Unknown error') if isinstance(search_response, dict) else search_response}")
            return None
        except Exception as e:
            logger.error(f"Error searching scrip: {e}")
            return None
    
    def get_ltp(self, exchange: str, symbol: str, token: str) -> Optional[float]:
        """Get last traded price for a symbol."""
        try:
            # Get quote data
            quote_response = self.client.getQuotes(
                mode='LTP',
                exch=exchange,
                token=token
            )
            
            if quote_response and quote_response.get('status') == 'success':
                ltp = quote_response.get('data', {}).get('ltp')
                if ltp:
                    return float(ltp)
            
            logger.error(f"Failed to get LTP for {symbol}: {quote_response.get('message', 'Unknown error') if isinstance(quote_response, dict) else quote_response}")
            return None
        except Exception as e:
            logger.error(f"Error fetching LTP for {symbol}: {e}")
            return None
    
    def place_order(
        self,
        exchange: str,
        token: str,
        symbol: str,
        side: str,  # 'BUY' or 'SELL'
        quantity: int,
        price: float,
        order_type: str = 'LIMIT',  # 'LIMIT', 'MARKET'
    ) -> Optional[Dict[str, Any]]:
        """Place an order on Kotak Neo."""
        try:
            if not self.client:
                logger.error("Client not initialized; call login() first")
                return None
            
            order_response = self.client.placeOrder(
                exch=exchange,
                token=token,
                side=side,
                ordtype=order_type,
                qty=quantity,
                price=price if order_type == 'LIMIT' else 0,
                pcode='MIS'  # MIS for intraday, CNC for delivery
            )
            
            if order_response and order_response.get('status') == 'success':
                logger.info(f"Order placed successfully: {order_response}")
                return order_response.get('data')
            else:
                logger.error(f"Order placement failed: {order_response.get('message', 'Unknown error') if isinstance(order_response, dict) else order_response}")
                return None
                
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    def cancel_order(self, exchange: str, order_id: str, token: str) -> bool:
        """Cancel an existing order."""
        try:
            if not self.client:
                logger.error("Client not initialized; call login() first")
                return False
            
            cancel_response = self.client.cancelOrder(
                exch=exchange,
                ordid=order_id,
                token=token
            )
            
            if cancel_response and cancel_response.get('status') == 'success':
                logger.info(f"Order cancelled successfully: {order_id}")
                return True
            else:
                logger.error(f"Cancel failed: {cancel_response.get('message', 'Unknown error') if isinstance(cancel_response, dict) else cancel_response}")
                return False
                
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False
    
    def get_positions(self) -> Optional[List[Dict[str, Any]]]:
        """Get current open positions."""
        try:
            if not self.client:
                logger.error("Client not initialized; call login() first")
                return None
            
            position_response = self.client.getPositions()
            
            if position_response and position_response.get('status') == 'success':
                return position_response.get('data', [])
            
            logger.error(f"Failed to get positions: {position_response.get('message', 'Unknown error') if isinstance(position_response, dict) else position_response}")
            return None
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return None
