# 🎯 Angel One Integration - Complete Setup

Your trading algorithm is now ready for live execution! Here's what's been set up:

## ✅ What's Working

1. **Strategy Engine**
   - Double-top/double-bottom pattern detection
   - ATM OI analysis (call/put)
   - Futures OI unwinding detection
   - Signal generation for 3 situations (bullish + bearish)

2. **Angel One Integration**
   - SmartAPI SDK installed
   - Login/authentication system
   - Order placement functions
   - Position tracking
   - Dry-run safety mode

3. **Configuration System**
   - Secure credential storage
   - .gitignore protection
   - Flexible trading parameters

## 🔐 Next Steps: Add Your Credentials

### 1. Open config.yaml and replace:

```yaml
angelone:
  api_key: "YOUR_ACTUAL_API_KEY"      # From smartapi.angelbroking.com
  client_id: "YOUR_CLIENT_CODE"        # Your Angel One login ID
  password: "YOUR_PASSWORD"            # Your Angel One password
  totp_secret: "YOUR_TOTP_SECRET"      # Optional but recommended
```

### 2. Get Credentials From:
🔗 **https://smartapi.angelbroking.com/**

- Login with your Angel One account
- Go to "My API" section
- Create new app if needed
- Copy API Key (Private Key)
- Your Client ID is your Angel One client code

### 3. Test First (IMPORTANT!)

**Always start with dry-run:**
```bash
"/Users/sabirnayak/Desktop/Algo Trading/.venv/bin/python" -m src.backtest.runner \
  --candles examples/data/candles.csv \
  --oi examples/data/oi.csv \
  --futures examples/data/futures_oi.csv \
  --execute --dry-run
```

**Look for:** ✅ "Successfully logged in to Angel One"

## 📁 Files You Need to Know

| File | Purpose |
|------|---------|
| [config.yaml](config.yaml) | **ADD YOUR CREDENTIALS HERE** |
| [QUICKSTART.md](QUICKSTART.md) | Quick command reference |
| [ANGEL_ONE_SETUP.md](ANGEL_ONE_SETUP.md) | Detailed setup guide |
| [README.md](README.md) | Strategy documentation |

## 🎮 Commands Cheat Sheet

**Backtest only (no login):**
```bash
python -m src.backtest.runner --candles FILE --oi FILE --futures FILE
```

**Dry run with Angel One (test login, no orders):**
```bash
python -m src.backtest.runner --candles FILE --oi FILE --futures FILE --execute --dry-run
```

**Live trading (REAL ORDERS):**
```bash
# Set dry_run: false in config.yaml first!
python -m src.backtest.runner --candles FILE --oi FILE --futures FILE --execute
```

## ⚠️  Critical Safety Features

1. **Dry Run Mode** - Test without real orders
2. **Demo Detection** - Blocks live trading with demo credentials  
3. **Position Limits** - Configurable in config.yaml
4. **Logging** - All actions logged to logs/

## 🔄 Live Data Integration (TODO)

Currently uses CSV files. For live trading you'll need:

1. **Real-time Candles**
   - WebSocket from Angel One
   - Or poll LTP every minute
   - Save to CSV or process in memory

2. **Live OI Data**
   - NSE website scraping
   - Or third-party OI data providers
   - Update every minute

3. **Futures OI**
   - From NSE reports
   - Current + next month contracts

## 📊 Example Live Workflow

```python
# Pseudo-code for live integration
while market_open:
    # 1. Fetch latest 1-min candle
    candle = fetch_live_candle(symbol="NIFTY")
    
    # 2. Get current ATM OI
    oi = fetch_oi_data(strike=get_atm_strike())
    
    # 3. Get futures OI
    fut_oi = fetch_futures_oi()
    
    # 4. Run strategy
    signal = strategy.evaluate(candles, oi, fut_oi)
    
    # 5. Execute if signal
    if signal and signal.action == "sell_strangle":
        order_manager.execute_signal(signal, current_price)
    
    sleep(60)  # Wait for next candle
```

## 🆘 Support

**Angel One API:**
- Portal: https://smartapi.angelbroking.com/
- Docs: https://smartapi.angelbroking.com/docs
- Support: support@angelbroking.com

**Application Issues:**
1. Check logs in `logs/` directory
2. Review ANGEL_ONE_SETUP.md
3. Verify credentials in config.yaml
4. Test with --dry-run first

## ⚡ Ready to Trade?

1. ✅ Add credentials to config.yaml
2. ✅ Test with --dry-run
3. ✅ Verify login works
4. ✅ Understand the strategy
5. ✅ Set risk limits
6. ⚠️  Start small!

---

**Remember:** Options trading is risky. Test thoroughly. Never trade more than you can afford to lose.

Good luck! 🚀
