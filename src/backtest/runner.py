import argparse
import logging
import sys
import yaml
from pathlib import Path
import pandas as pd

from src.data.models import Candle, OIData, FuturesOI
from src.strategies.non_directional_strangle import NonDirectionalStrangleStrategy
from src.brokers.angelone import AngelOneClient
from src.execution.order_manager import OrderManager
from src.utils.config_validator import ConfigValidator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        logger.info("Please copy config.template.yaml to config.yaml and fill in your details")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        sys.exit(1)


def load_candles(path: str):
    df = pd.read_csv(path)
    candles = [
        Candle(
            timestamp=str(r.timestamp),
            open=float(r.open),
            high=float(r.high),
            low=float(r.low),
            close=float(r.close),
        )
        for r in df.itertuples(index=False)
    ]
    return candles


def load_oi(path: str):
    df = pd.read_csv(path)
    oi = [
        OIData(
            timestamp=str(r.timestamp),
            oi_call_atm=float(r.oi_call_atm),
            oi_put_atm=float(r.oi_put_atm),
        )
        for r in df.itertuples(index=False)
    ]
    return oi


def load_futures(path: str):
    df = pd.read_csv(path)
    fut = [
        FuturesOI(
            timestamp=str(r.timestamp),
            current_month_oi=float(r.current_month_oi),
            next_month_oi=float(r.next_month_oi),
        )
        for r in df.itertuples(index=False)
    ]
    return fut


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candles", required=True)
    parser.add_argument("--oi", required=True)
    parser.add_argument("--futures", required=True)
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--execute", action="store_true", help="Execute live orders via Angel One")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode (no actual orders)")
    args = parser.parse_args()

    candles = load_candles(args.candles)
    oi = load_oi(args.oi)
    fut = load_futures(args.futures)

    # Align by timestamps (simple truncation to min len)
    min_len = min(len(candles), len(oi), len(fut))
    candles = candles[:min_len]
    oi = oi[:min_len]
    fut = fut[:min_len]

    strat = NonDirectionalStrangleStrategy()
    
    # Initialize broker and order manager if executing
    order_manager = None
    if args.execute:
        config = load_config(args.config)
        
        # Validate configuration
        try:
            ConfigValidator.validate_and_raise(config)
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            sys.exit(1)
        
        # Check if using demo credentials
        angel_config = config.get('angelone', {})
        if angel_config.get('api_key', '').startswith('DEMO_'):
            logger.warning("=" * 70)
            logger.warning("DEMO CREDENTIALS DETECTED")
            logger.warning("Please update config.yaml with your actual Angel One credentials")
            logger.warning("Get credentials from: https://smartapi.angelbroking.com/")
            logger.warning("=" * 70)
            if not args.dry_run:
                logger.error("Cannot execute real orders with demo credentials")
                sys.exit(1)
        
        # Initialize Angel One client
        broker = AngelOneClient(
            api_key=angel_config.get('api_key', ''),
            client_id=angel_config.get('client_id', ''),
            password=angel_config.get('password', ''),
            totp_secret=angel_config.get('totp_secret'),
        )
        
        # Only attempt login if not using demo credentials in dry-run
        if not angel_config.get('api_key', '').startswith('DEMO_'):
            if not broker.login():
                logger.error("Failed to login to Angel One. Check your credentials.")
                sys.exit(1)
            logger.info("Successfully logged in to Angel One")
        else:
            logger.info("Skipping login in demo mode")
        
        # Initialize order manager
        trading_config = config.get('trading', {})
        order_manager = OrderManager(
            broker=broker,
            underlying_symbol=trading_config.get('underlying_symbol', 'NIFTY'),
            exchange=trading_config.get('exchange', 'NFO'),
            lot_size=trading_config.get('lot_size', 50),
            max_loss_per_trade=trading_config.get('max_loss_per_trade', 5000),
            capital=trading_config.get('capital', 1000000),  # Default 10 lakhs
            dry_run=args.dry_run or trading_config.get('dry_run', True),
        )

    # Iterate and evaluate
    signals = []
    for i in range(4, min_len + 1):
        sig = strat.evaluate(candles[:i], oi[:i], fut[:i])
        if sig:
            signals.append(sig)
            print(
                f"{sig.timestamp} | {sig.action} | {sig.context.get('reason')} | "
                f"call_dist={sig.call_distance} put_dist={sig.put_distance}"
            )
            
            # Execute if order manager is initialized
            if order_manager and sig.action == "sell_strangle":
                current_price = candles[i-1].close
                order_manager.execute_signal(sig, current_price)

    if not signals:
        print("No signals found.")
    
    # Cleanup
    if args.execute and order_manager:
        logger.info("\n" + "=" * 60)
        logger.info("Positions summary:")
        print(order_manager.get_positions_summary())
        if not angel_config.get('api_key', '').startswith('DEMO_'):
            order_manager.broker.logout()
        logger.info("=" * 60)


if __name__ == "__main__":
    main()
