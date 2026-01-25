"""Configuration validation for the trading bot."""
import logging
from typing import Dict, Any, List, Tuple
from src.utils.error_handler import ConfigurationError, ValidationError

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validates trading bot configuration."""
    
    REQUIRED_FIELDS = {
        'angelone': ['api_key', 'client_id', 'password'],
        'trading': ['underlying_symbol', 'exchange', 'lot_size', 'capital', 'dry_run']
    }
    
    VALID_EXCHANGES = ['NFO', 'NSE', 'BSE', 'MCX']
    VALID_PRODUCT_TYPES = ['INTRADAY', 'CARRYFORWARD', 'DELIVERY']
    VALID_SYMBOLS = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY']
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate entire configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Check required sections
        if 'angelone' not in config:
            errors.append("Missing 'angelone' configuration section")
        if 'trading' not in config:
            errors.append("Missing 'trading' configuration section")
            
        if errors:
            return False, errors
            
        # Validate Angel One credentials
        angelone_errors = ConfigValidator._validate_angelone(config['angelone'])
        errors.extend(angelone_errors)
        
        # Validate trading parameters
        trading_errors = ConfigValidator._validate_trading(config['trading'])
        errors.extend(trading_errors)
        
        return len(errors) == 0, errors
        
    @staticmethod
    def _validate_angelone(config: Dict[str, Any]) -> List[str]:
        """Validate Angel One configuration."""
        errors = []
        
        for field in ConfigValidator.REQUIRED_FIELDS['angelone']:
            if field not in config:
                errors.append(f"Missing required Angel One field: '{field}'")
            elif not config[field] or config[field] == '':
                errors.append(f"Angel One field '{field}' cannot be empty")
            elif isinstance(config[field], str) and config[field].startswith('YOUR_'):
                errors.append(f"Angel One field '{field}' still has template value. Please update with actual credentials.")
                
        # Check API key format (basic validation)
        if 'api_key' in config and config['api_key']:
            if len(config['api_key']) < 10:
                errors.append("Angel One API key seems too short. Please verify.")
                
        # TOTP is optional but if provided should not be empty
        if 'totp_secret' in config and config['totp_secret'] == '':
            logger.warning("TOTP secret is empty. TOTP-based authentication will not be used.")
            
        return errors
        
    @staticmethod
    def _validate_trading(config: Dict[str, Any]) -> List[str]:
        """Validate trading configuration."""
        errors = []
        
        # Check required fields
        for field in ConfigValidator.REQUIRED_FIELDS['trading']:
            if field not in config:
                errors.append(f"Missing required trading field: '{field}'")
                
        # Validate underlying symbol
        if 'underlying_symbol' in config:
            symbol = config['underlying_symbol']
            if symbol not in ConfigValidator.VALID_SYMBOLS:
                logger.warning(
                    f"Underlying symbol '{symbol}' is not in standard list: {ConfigValidator.VALID_SYMBOLS}. "
                    "Proceeding anyway but verify symbol is correct."
                )
                
        # Validate exchange
        if 'exchange' in config:
            exchange = config['exchange']
            if exchange not in ConfigValidator.VALID_EXCHANGES:
                errors.append(
                    f"Invalid exchange '{exchange}'. Must be one of: {ConfigValidator.VALID_EXCHANGES}"
                )
                
        # Validate lot size
        if 'lot_size' in config:
            lot_size = config['lot_size']
            if not isinstance(lot_size, int) or lot_size <= 0:
                errors.append(f"Lot size must be a positive integer, got: {lot_size}")
            elif lot_size > 1000:
                logger.warning(f"Lot size {lot_size} seems very large. Please verify.")
                
        # Validate capital
        if 'capital' in config:
            capital = config['capital']
            if not isinstance(capital, (int, float)) or capital <= 0:
                errors.append(f"Capital must be a positive number, got: {capital}")
            elif capital < 100000:
                logger.warning(f"Capital ₹{capital:,.0f} is quite low for options trading.")
                
        # Validate max loss per trade
        if 'max_loss_per_trade' in config:
            max_loss = config['max_loss_per_trade']
            if not isinstance(max_loss, (int, float)) or max_loss <= 0:
                errors.append(f"Max loss per trade must be a positive number, got: {max_loss}")
            elif 'capital' in config:
                capital = config['capital']
                if max_loss > capital * 0.05:  # More than 5% of capital
                    logger.warning(
                        f"Max loss per trade (₹{max_loss:,.0f}) is > 5% of capital "
                        f"(₹{capital:,.0f}). This is risky."
                    )
                    
        # Validate product type
        if 'product_type' in config:
            product_type = config['product_type']
            if product_type not in ConfigValidator.VALID_PRODUCT_TYPES:
                errors.append(
                    f"Invalid product type '{product_type}'. "
                    f"Must be one of: {ConfigValidator.VALID_PRODUCT_TYPES}"
                )
                
        # Validate dry run flag
        if 'dry_run' in config:
            dry_run = config['dry_run']
            if not isinstance(dry_run, bool):
                errors.append(f"dry_run must be boolean (true/false), got: {dry_run}")
            elif dry_run is False:
                logger.warning(
                    "⚠️  DRY RUN IS DISABLED! Real orders will be placed. "
                    "Ensure this is intentional."
                )
                
        # Validate hedge settings if present
        if 'enable_hedge' in config and config['enable_hedge']:
            if 'hedge_distance' not in config or config['hedge_distance'] <= 0:
                errors.append("Hedging enabled but hedge_distance not set or invalid")
                
        return errors
        
    @staticmethod
    def validate_and_raise(config: Dict[str, Any]) -> None:
        """
        Validate configuration and raise exception if invalid.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        is_valid, errors = ConfigValidator.validate_config(config)
        
        if not is_valid:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
            
        logger.info("✓ Configuration validation passed")


def validate_strike_distance(
    call_distance: int,
    put_distance: int,
    current_price: float,
    min_distance: int = 50,
    max_distance: int = 2000
) -> None:
    """
    Validate strike distances.
    
    Args:
        call_distance: Distance for call strike
        put_distance: Distance for put strike
        current_price: Current underlying price
        min_distance: Minimum allowed distance
        max_distance: Maximum allowed distance
        
    Raises:
        ValidationError: If strike distances are invalid
    """
    if call_distance < min_distance:
        raise ValidationError(
            f"Call strike distance {call_distance} is below minimum {min_distance}",
            field="call_distance"
        )
        
    if put_distance < min_distance:
        raise ValidationError(
            f"Put strike distance {put_distance} is below minimum {min_distance}",
            field="put_distance"
        )
        
    if call_distance > max_distance:
        raise ValidationError(
            f"Call strike distance {call_distance} exceeds maximum {max_distance}",
            field="call_distance"
        )
        
    if put_distance > max_distance:
        raise ValidationError(
            f"Put strike distance {put_distance} exceeds maximum {max_distance}",
            field="put_distance"
        )
        
    # Check if strikes are too close (potential for large losses)
    if call_distance < current_price * 0.01 or put_distance < current_price * 0.01:
        logger.warning(
            f"Strike distances ({call_distance}, {put_distance}) are very close to ATM. "
            f"This increases risk significantly."
        )


def validate_capital_sufficiency(
    capital: float,
    lot_size: int,
    estimated_margin_per_lot: float = 50000  # Conservative estimate for NIFTY
) -> None:
    """
    Validate that capital is sufficient for trading.
    
    Args:
        capital: Available capital
        lot_size: Number of lots to trade
        estimated_margin_per_lot: Estimated margin requirement per lot
        
    Raises:
        ValidationError: If capital is insufficient
    """
    required_margin = lot_size * estimated_margin_per_lot
    
    if capital < required_margin:
        raise ValidationError(
            f"Insufficient capital. Required: ₹{required_margin:,.0f}, Available: ₹{capital:,.0f}",
            field="capital"
        )
        
    if capital < required_margin * 1.5:
        logger.warning(
            f"Capital (₹{capital:,.0f}) is close to minimum margin requirement "
            f"(₹{required_margin:,.0f}). Consider increasing capital for safety."
        )
