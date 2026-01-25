"""Error handling framework for the trading bot."""
import time
import logging
from typing import Callable, Any, TypeVar, Optional
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)

# Type variable for generic retry decorator
T = TypeVar('T')


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TradingBotError(Exception):
    """Base exception for all trading bot errors."""
    
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM, **kwargs):
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.context = kwargs


class BrokerError(TradingBotError):
    """Errors related to broker API interactions."""
    
    def __init__(self, message: str, broker: str = "unknown", **kwargs):
        super().__init__(message, ErrorSeverity.HIGH, broker=broker, **kwargs)


class DataError(TradingBotError):
    """Errors related to data fetching or validation."""
    
    def __init__(self, message: str, data_source: str = "unknown", **kwargs):
        super().__init__(message, ErrorSeverity.HIGH, data_source=data_source, **kwargs)


class StrategyError(TradingBotError):
    """Errors related to strategy execution."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorSeverity.MEDIUM, **kwargs)


class ConfigurationError(TradingBotError):
    """Errors related to configuration issues."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorSeverity.CRITICAL, **kwargs)


class ValidationError(TradingBotError):
    """Errors related to input validation."""
    
    def __init__(self, message: str, field: str = "unknown", **kwargs):
        super().__init__(message, ErrorSeverity.MEDIUM, field=field, **kwargs)


class CircuitBreaker:
    """Circuit breaker pattern implementation for API calls."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to catch
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half-open
        
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call function with circuit breaker protection.
        
        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            BrokerError: If circuit is open
            Original exception if circuit breaker allows
        """
        if self.state == "open":
            if time.time() - self.last_failure_time < self.recovery_timeout:
                raise BrokerError(
                    f"Circuit breaker is OPEN. Too many failures. "
                    f"Wait {self.recovery_timeout}s before retry."
                )
            else:
                self.state = "half-open"
                logger.info("Circuit breaker entering HALF-OPEN state")
        
        try:
            result = func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
                logger.info("Circuit breaker reset to CLOSED state")
            return result
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.error(
                    f"Circuit breaker opened after {self.failure_count} failures"
                )
            raise e


def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
    logger_instance: Optional[logging.Logger] = None
) -> Callable:
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff calculation
        exceptions: Tuple of exception types to catch and retry
        logger_instance: Logger to use for logging retry attempts
        
    Returns:
        Decorated function
        
    Example:
        @retry(max_attempts=3, initial_delay=1.0, exceptions=(BrokerError,))
        def fetch_data():
            # ... code that might fail
            pass
    """
    log = logger_instance or logger
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        log.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts. "
                            f"Error: {str(e)}"
                        )
                        raise
                    
                    log.warning(
                        f"Function {func.__name__} failed (attempt {attempt}/{max_attempts}). "
                        f"Retrying in {delay:.1f}s. Error: {str(e)}"
                    )
                    
                    time.sleep(delay)
                    delay = min(delay * exponential_base, max_delay)
            
            # This should never be reached, but satisfies type checker
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


class ErrorHandler:
    """Central error handling and reporting."""
    
    def __init__(self, alert_callback: Optional[Callable] = None):
        """
        Initialize error handler.
        
        Args:
            alert_callback: Optional callback function for critical errors
        """
        self.alert_callback = alert_callback
        self.error_counts = {}
        
    def handle_error(
        self,
        error: Exception,
        context: str = "",
        suppress: bool = False
    ) -> None:
        """
        Handle error with appropriate logging and alerting.
        
        Args:
            error: Exception to handle
            context: Context where error occurred
            suppress: Whether to suppress re-raising the exception
        """
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        if isinstance(error, TradingBotError):
            severity = error.severity
            message = f"[{context}] {error.message}"
            
            if severity == ErrorSeverity.CRITICAL:
                logger.critical(message, exc_info=True)
                if self.alert_callback:
                    self.alert_callback(message, severity)
            elif severity == ErrorSeverity.HIGH:
                logger.error(message, exc_info=True)
                if self.alert_callback and self.error_counts[error_type] >= 3:
                    self.alert_callback(message, severity)
            elif severity == ErrorSeverity.MEDIUM:
                logger.warning(message)
            else:
                logger.info(message)
        else:
            logger.error(f"[{context}] Unhandled exception: {str(error)}", exc_info=True)
            
        if not suppress:
            raise error
            
    def get_error_summary(self) -> dict:
        """Get summary of error counts."""
        return self.error_counts.copy()
