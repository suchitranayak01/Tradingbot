# Quick Start - Angel One Trading

## 🔧 Initial Setup (One-time)

1. **Get API Credentials**
   - Visit: https://smartapi.angelbroking.com/
   - Generate API Key
   - Note: API Key, Client ID, Password, TOTP Secret

2. **Configure**
   ```bash
   cd "/Users/sabirnayak/Desktop/Algo Trading"
   cp config.template.yaml config.yaml
   # Edit config.yaml with your credentials
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 🧪 Testing (Dry Run)

**Test without placing real orders:**
```bash
"/Users/sabirnayak/Desktop/Algo Trading/.venv/bin/python" -m src.backtest.runner \
  --candles examples/data/candles.csv \
  --oi examples/data/oi.csv \
  --futures examples/data/futures_oi.csv \
  --execute --dry-run
```

## 🚀 Live Trading (REAL MONEY)

**⚠️  WARNING: This will place actual orders**

1. Set `dry_run: false` in config.yaml
2. Run:
```bash
"/Users/sabirnayak/Desktop/Algo Trading/.venv/bin/python" -m src.backtest.runner \
  --candles path/to/live/candles.csv \
  --oi path/to/live/oi.csv \
  --futures path/to/live/futures.csv \
  --execute
```

## 📊 What It Does

When a signal is detected:
- **Situation 1:** No trade (false signal)
- **Situation 2:** Sell Call + Put at equal distance
- **Situation 3:** Sell Call (closer) + Put (farther)

## 🔍 Monitor

- Check logs in: `logs/YYYY-MM-DD/`
- Verify orders in Angel One app/web
- Watch positions in real-time

## ⚠️  Important

- Start with small position sizes
- Test extensively in dry-run first
- Monitor all positions actively
- Set stop losses manually
- Options trading involves substantial risk

## 🆘 Troubleshooting

| Error | Solution |
|-------|----------|
| "Invalid totp" | Check TOTP secret or remove if not using |
| "Insufficient margin" | Reduce lot_size in config.yaml |
| "Symbol not found" | Need symbol master file (see ANGEL_ONE_SETUP.md) |
| Login fails | Verify API key, client ID, password |

## 📚 More Info

- Full setup: [ANGEL_ONE_SETUP.md](ANGEL_ONE_SETUP.md)
- Strategy details: [README.md](README.md)
- Angel One Docs: https://smartapi.angelbroking.com/docs
