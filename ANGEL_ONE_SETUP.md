# Angel One Setup Guide

## Step-by-Step Setup for Live Trading

### 1. Create Angel One Account
1. Visit [Angel One](https://www.angelone.in/)
2. Sign up for a demat and trading account
3. Complete KYC verification

### 2. Generate API Credentials

#### A. Login to Angel One SmartAPI Portal
1. Go to [SmartAPI Portal](https://smartapi.angelbroking.com/)
2. Login with your Angel One credentials
3. Navigate to **My API** or **API Keys** section

#### B. Generate API Key
1. Click on "Create New App" or "Generate API Key"
2. Fill in application details:
   - App Name: "Algo Trading Bot"
   - Redirect URL: http://localhost (for now)
   - Description: "Automated trading system"
3. Submit and note down:
   - **API Key** (also called Private Key)
   - **Client ID** (your Angel One client code)

#### C. Get Your TOTP Secret (Optional but Recommended)
1. In SmartAPI portal, enable TOTP-based authentication
2. Scan the QR code with an authenticator app (Google Authenticator, Authy)
3. **Save the secret key** (usually shown as a text string below QR)
   - Example format: `JBSWY3DPEHPK3PXP`

### 3. Configure Application

#### A. Copy Configuration Template
```bash
cd "/Users/sabirnayak/Desktop/Algo Trading"
cp config.template.yaml config.yaml
```

#### B. Edit config.yaml
Replace the placeholder values with your actual credentials:

```yaml
angelone:
  # From SmartAPI portal
  api_key: "YOUR_ACTUAL_API_KEY_HERE"
  
  # Your Angel One client ID (login ID)
  client_id: "YOUR_CLIENT_ID"
  
  # Your Angel One password
  password: "YOUR_PASSWORD"
  
  # TOTP secret (if enabled) - HIGHLY RECOMMENDED
  totp_secret: "YOUR_TOTP_SECRET_KEY"

trading:
  underlying_symbol: "NIFTY"
  exchange: "NFO"
  lot_size: 50  # NIFTY lot size (verify current value)
  max_loss_per_trade: 5000
  max_open_positions: 2
  dry_run: true  # KEEP THIS TRUE for testing
```

### 4. Security Best Practices

#### Important Security Notes:
1. **NEVER** commit `config.yaml` to git (already in .gitignore)
2. **NEVER** share your API credentials
3. Set file permissions to restrict access:
   ```bash
   chmod 600 config.yaml
   ```
4. Consider using environment variables for production:
   ```bash
   export ANGEL_API_KEY="your_key"
   export ANGEL_CLIENT_ID="your_id"
   export ANGEL_PASSWORD="your_pass"
   ```

### 5. Test Your Setup

#### A. Test with Dry Run (Recommended First)
```bash
cd "/Users/sabirnayak/Desktop/Algo Trading"

# This will validate login but NOT place real orders
"/Users/sabirnayak/Desktop/Algo Trading/.venv/bin/python" -m src.backtest.runner \
  --candles examples/data/candles.csv \
  --oi examples/data/oi.csv \
  --futures examples/data/futures_oi.csv \
  --execute --dry-run
```

**Expected Output:**
- Login successful message
- Signal detection
- "[DRY RUN] Would place orders:" messages
- No actual orders placed

#### B. Verify Credentials Work
If you see:
- ✅ "Successfully logged in to Angel One" → Credentials are correct
- ❌ "Invalid totp" → Check your TOTP secret
- ❌ "Invalid credentials" → Check API key, client ID, or password
- ❌ "API key not found" → Regenerate API key from portal

### 6. Go Live (Use With Extreme Caution)

⚠️  **WARNING: Real Money Trading**

Only proceed after:
1. Thoroughly testing with dry-run mode
2. Understanding the strategy logic
3. Setting appropriate risk limits
4. Having sufficient trading capital

#### Steps:
1. Edit `config.yaml`:
   ```yaml
   trading:
     dry_run: false  # Change to false
   ```

2. Run with live execution:
   ```bash
   "/Users/sabirnayak/Desktop/Algo Trading/.venv/bin/python" -m src.backtest.runner \
     --candles examples/data/candles.csv \
     --oi examples/data/oi.csv \
     --futures examples/data/futures_oi.csv \
     --execute
   ```

3. Monitor orders in Angel One app/web platform

### 7. Common Issues and Solutions

#### Issue: "Invalid totp"
**Solution:**
- If not using TOTP, remove `totp_secret` line or set to empty string
- If using TOTP, verify the secret key is correct
- Ensure your system time is accurate (TOTP is time-based)

#### Issue: "API limit exceeded"
**Solution:**
- Angel One has rate limits (typically 1 req/sec)
- Add delays between API calls if processing many signals

#### Issue: "Symbol not found"
**Solution:**
- Option symbols need exact format (NIFTY26JAN23500CE)
- Download Angel One symbol master file
- Use `searchScrip` API to find exact tokens

#### Issue: "Insufficient margin"
**Solution:**
- Ensure adequate funds in your Angel One account
- Reduce lot size in config.yaml
- Check margin requirements for option selling

### 8. Symbol Master File (Required for Production)

For accurate symbol/token mapping:

1. Download symbol master from Angel One:
   ```bash
   curl -o symbols.csv "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
   ```

2. Parse and cache symbols in your code
3. Update `_get_option_symbol()` in [order_manager.py](src/execution/order_manager.py)

### 9. Monitoring and Logging

- Logs are saved to: `logs/YYYY-MM-DD/`
- Monitor Angel One app for order status
- Check positions regularly
- Set up alerts for unusual activity

### 10. Risk Disclaimer

⚠️  **READ CAREFULLY:**

- Options trading involves substantial risk
- You can lose more than your initial investment
- This software is for educational purposes
- No guarantee of profits
- Test extensively before live trading
- Start with small position sizes
- Never risk money you cannot afford to lose
- Consider consulting a financial advisor

---

## Support

For Angel One API issues:
- Documentation: https://smartapi.angelbroking.com/docs
- Support: support@angelbroking.com
- Portal: https://smartapi.angelbroking.com/

For this application:
- Check README.md
- Review source code in src/
- Test thoroughly in dry-run mode
