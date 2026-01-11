# 🌐 Web Dashboard - Quick Start

## Your Dashboard is Ready! 🎉

### 🚀 Open the Dashboard

Click this link or copy to your browser:

**👉 http://localhost:8501**

---

## What You Can Do

### 1️⃣ Configure Credentials
- Enter your Angel One API credentials in the sidebar
- Set trading parameters (lot size, max loss, etc.)
- Save configuration

### 2️⃣ Test Connection
- Click "Test Angel One Connection" to verify credentials
- See connection status in real-time

### 3️⃣ Upload Data & Test
- Upload your candles, OI, and futures CSV files
- Click "Process Data" to generate signals
- View signals in the "Signals" tab

### 4️⃣ Start Trading Bot
- Toggle "Dry Run Mode" for safe testing
- Click "▶️ START BOT" to begin
- Monitor signals and positions in real-time

---

## Dashboard Features

| Feature | Description |
|---------|-------------|
| 📊 Signals | View all trading signals with timestamps |
| 💼 Positions | Track active positions and orders |
| 📈 Charts | Visual analysis of price and OI data |
| 📝 Logs | Real-time activity logs |
| ⚙️ Config | Manage credentials and parameters |
| 🔌 Connection | Test broker connectivity |

---

## Alternative: Command Line Start

If the dashboard isn't running, start it manually:

```bash
cd "/Users/sabirnayak/Desktop/Algo Trading"

# Option 1: Use the launcher script
./start_dashboard.sh

# Option 2: Direct command
"/Users/sabirnayak/Desktop/Algo Trading/.venv/bin/python" -m streamlit run dashboard.py
```

---

## Stop the Dashboard

**In your browser:** Just close the tab

**In Terminal:** Press `Ctrl+C` or run:
```bash
pkill -f streamlit
```

---

## Next Steps

1. **Open:** http://localhost:8501
2. **Configure:** Add your Angel One credentials
3. **Test:** Upload example CSV files or your own data
4. **Monitor:** Watch signals appear in real-time
5. **Trade:** Start the bot when ready

---

## 🎯 Current Status

✅ Dashboard is running at: **http://localhost:8501**

You can now control your trading bot from your browser!
