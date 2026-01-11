# Non-Directional Strangle Strategy (OI + Price Action)

This project implements a Python trading algorithm that identifies ends of bullish/bearish trends using small-timeframe price patterns, options ATM OI shifts, and futures OI structure changes. It emits non-directional strangle entry signals and can execute live orders via Angel One (Angel Broking).

## Key Concepts
- Price moves in waves; consolidation/accumulation precedes continuation or reversal.
- End of bullish trend: double-top + rising ATM call OI + combined futures OI drop (long unwinding).
- End of bearish trend: double-bottom + rising ATM put OI + combined futures OI drop.
- Signals:
  - Situation 1 (bullish): Double-top but ATM call OI falling and futures OI stable → no trade (trend continues).
  - Situation 2 (bullish): Double-top + rising ATM call OI → sell strangle at equal distance.
  - Situation 3 (bullish): Double-top + rising ATM call OI + combined futures OI dropping → sell strangle with call strike closer than put.
  - Bearish analogs mirror the logic with puts and lows.

## Quick Start

### 1) Install dependencies
```bash
pip install -r requirements.txt
```

### 2) Backtest mode (no real orders)
```bash
python -m src.backtest.runner --candles examples/data/candles.csv \
  --oi examples/data/oi.csv \
  --futures examples/data/futures_oi.csv
```

### 3) Live Trading Setup with Angel One

#### A. Get Angel One Credentials
1. Sign up at [Angel One](https://www.angelone.in/)
2. Generate API credentials:
   - Login to Angel One → Profile → My API
   - Note down: **API Key**, **Client ID**, **Password**
   - (Optional) Setup TOTP for enhanced security

#### B. Configure Credentials
```bash
# Copy template
cp config.template.yaml config.yaml

# Edit config.yaml with your credentials
# IMPORTANT: Never commit config.yaml to git (already in .gitignore)
```

Edit `config.yaml`:
```yaml
angelone:
  api_key: "your_actual_api_key"
  client_id: "your_client_id"
  password: "your_password"
  totp_secret: "your_totp_secret"  # Optional

trading:
  underlying_symbol: "NIFTY"
  exchange: "NFO"
  lot_size: 50
  max_loss_per_trade: 5000
  dry_run: true  # Set to false for real orders
```

#### C. Run with Order Execution

**Dry run mode (recommended first):**
```bash
python -m src.backtest.runner \
  --candles examples/data/candles.csv \
  --oi examples/data/oi.csv \
  --futures examples/data/futures_oi.csv \
  --execute --dry-run
```

**Live execution (REAL MONEY):**
```bash
# ⚠️  WARNING: This will place actual orders on your Angel One account
# Make sure dry_run: false in config.yaml
python -m src.backtest.runner \
  --candles examples/data/candles.csv \
  --oi examples/data/oi.csv \
  --futures examples/data/futures_oi.csv \
  --execute
```

## Data Format
- candles.csv: `timestamp,open,high,low,close` (1-minute bars)
- oi.csv: `timestamp,oi_call_atm,oi_put_atm`
- futures_oi.csv: `timestamp,current_month_oi,next_month_oi`

## Important Notes

### Security
- **NEVER commit `config.yaml`** - it's already in `.gitignore`
- Store credentials securely
- Use TOTP for additional security
- Review all orders in dry-run mode first

### Symbol Mapping
- The current implementation uses simplified symbol construction
- For production, you should:
  1. Download Angel One's symbol master file
  2. Or use `searchScrip` API to get exact tokens
  3. Implement proper expiry calculation (weekly/monthly)

### Risk Management
- Start with `dry_run: true` in config
- Test thoroughly with paper trading
- Set appropriate `max_loss_per_trade` limits
- Monitor positions actively

### Live Data Integration
- Current setup uses CSV files for backtesting
- For live trading, integrate:
  - WebSocket feeds for real-time candles
  - Live OI data from NSE or broker APIs
  - Auto-refresh mechanism

## Project Structure
```
src/
├── brokers/
│   └── angelone.py          # Angel One API wrapper
├── execution/
│   └── order_manager.py     # Order execution logic
├── strategies/
│   └── non_directional_strangle.py
├── core/
│   ├── patterns.py          # Chart pattern detection
│   └── oi_analysis.py       # OI analysis
├── data/
│   └── models.py            # Data models
└── backtest/
    └── runner.py            # Main execution script
```

## Disclaimer
**⚠️  FOR EDUCATIONAL PURPOSES ONLY**

This software is provided as-is for educational and research purposes. Trading derivatives involves substantial risk of loss. The authors are not responsible for any financial losses incurred through the use of this software. Always:
- Test extensively in paper trading mode
- Understand the risks involved
- Never trade with money you cannot afford to lose
- Consult with a financial advisor

Use at your own risk.
