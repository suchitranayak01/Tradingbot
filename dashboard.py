import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import yaml
import json
from pathlib import Path
import threading
import time
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.strategies.non_directional_strangle import NonDirectionalStrangleStrategy, Signal
from src.brokers.angelone import AngelOneClient
from src.brokers.kotak_neo import KotakNeoClient
from src.execution.order_manager import OrderManager
from src.data.models import Candle, OIData, FuturesOI

# Page config
st.set_page_config(
    page_title="Algo Trading Bot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'bot_running' not in st.session_state:
    st.session_state.bot_running = False
if 'signals' not in st.session_state:
    st.session_state.signals = []
if 'positions' not in st.session_state:
    st.session_state.positions = []
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'broker_connected' not in st.session_state:
    st.session_state.broker_connected = False

# Sidebar - Configuration
st.sidebar.title("⚙️ Configuration")

# Add navigation section
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Stock Screeners")
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("📈 Trending", use_container_width=True):
        st.switch_page("pages/01_trending_screener.py")
with col2:
    if st.button("🔝 ATH Finder", use_container_width=True):
        st.switch_page("pages/02_ath_screener.py")
st.sidebar.markdown("---")

# Load existing config
config_path = Path("config.yaml")
if config_path.exists():
    with open(config_path) as f:
        config = yaml.safe_load(f) or {}
        # Ensure all keys exist
        if 'angelone' not in config:
            config['angelone'] = {}
        if 'kotak_neo' not in config:
            config['kotak_neo'] = {}
        if 'trading' not in config:
            config['trading'] = {}
else:
    config = {
        'broker': 'angelone',
        'angelone': {
            'api_key': '',
            'client_id': '',
            'password': '',
            'totp_secret': ''
        },
        'kotak_neo': {
            'api_key': '',
            'user_id': '',
            'password': '',
            'consumer_key': '',
            'consumer_secret': ''
        },
        'trading': {
            'underlying_symbol': 'NIFTY',
            'exchange': 'NFO',
            'lot_size': 50,
            'max_loss_per_trade': 5000,
            'dry_run': True
        }
    }

# Broker Selection
st.sidebar.subheader("🏦 Broker Selection")
broker_choice = st.sidebar.radio("Select Broker", ["Angel One", "Kotak Neo"], 
                                  index=0 if config.get('broker', 'angelone') == 'angelone' else 1)
config['broker'] = 'angelone' if broker_choice == 'Angel One' else 'kotak_neo'

# Angel One Credentials
if broker_choice == "Angel One":
    st.sidebar.subheader("🔐 Angel One Credentials")
    api_key = st.sidebar.text_input("API Key", value=config['angelone'].get('api_key', ''), type="password")
    client_id = st.sidebar.text_input("Client ID", value=config['angelone'].get('client_id', ''))
    password = st.sidebar.text_input("Password", value=config['angelone'].get('password', ''), type="password")
    totp_secret = st.sidebar.text_input("TOTP Secret (Optional)", value=config['angelone'].get('totp_secret', ''), type="password")
    broker_credentials = {
        'api_key': api_key,
        'client_id': client_id,
        'password': password,
        'totp_secret': totp_secret
    }
else:  # Kotak Neo
    st.sidebar.subheader("🔐 Kotak Neo Credentials")
    api_key = st.sidebar.text_input("API Key", value=config['kotak_neo'].get('api_key', ''), type="password")
    user_id = st.sidebar.text_input("User ID", value=config['kotak_neo'].get('user_id', ''))
    password = st.sidebar.text_input("Password", value=config['kotak_neo'].get('password', ''), type="password")
    consumer_key = st.sidebar.text_input("Consumer Key", value=config['kotak_neo'].get('consumer_key', ''), type="password")
    consumer_secret = st.sidebar.text_input("Consumer Secret", value=config['kotak_neo'].get('consumer_secret', ''), type="password")
    broker_credentials = {
        'api_key': api_key,
        'user_id': user_id,
        'password': password,
        'consumer_key': consumer_key,
        'consumer_secret': consumer_secret
    }

# Trading Parameters
st.sidebar.subheader("📊 Trading Parameters")
underlyings = ["NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX", "GOLD", "GOLDM", "SILVER", "SILVERM"]
underlying = st.sidebar.selectbox("Underlying", underlyings, 
                                   index=underlyings.index(config['trading'].get('underlying_symbol', 'NIFTY')))
exchange = st.sidebar.selectbox("Exchange", ["NFO", "NSE"], 
                                index=["NFO", "NSE"].index(config['trading'].get('exchange', 'NFO')))
lot_size = st.sidebar.number_input("Lot Size", min_value=1, max_value=1000, value=config['trading'].get('lot_size', 50))
max_loss = st.sidebar.number_input("Max Loss Per Trade (₹)", min_value=100, max_value=100000, value=config['trading'].get('max_loss_per_trade', 5000))
dry_run = st.sidebar.checkbox("Dry Run Mode (No Real Orders)", value=config['trading'].get('dry_run', True))

# Save config button
if st.sidebar.button("💾 Save Configuration"):
    new_config = {
        'broker': config['broker'],
        'angelone': {
            'api_key': broker_credentials.get('api_key', '') if broker_choice == "Angel One" else config['angelone'].get('api_key', ''),
            'client_id': broker_credentials.get('client_id', '') if broker_choice == "Angel One" else config['angelone'].get('client_id', ''),
            'password': broker_credentials.get('password', '') if broker_choice == "Angel One" else config['angelone'].get('password', ''),
            'totp_secret': broker_credentials.get('totp_secret', '') if broker_choice == "Angel One" else config['angelone'].get('totp_secret', '')
        },
        'kotak_neo': {
            'api_key': broker_credentials.get('api_key', '') if broker_choice == "Kotak Neo" else config['kotak_neo'].get('api_key', ''),
            'user_id': broker_credentials.get('user_id', '') if broker_choice == "Kotak Neo" else config['kotak_neo'].get('user_id', ''),
            'password': broker_credentials.get('password', '') if broker_choice == "Kotak Neo" else config['kotak_neo'].get('password', ''),
            'consumer_key': broker_credentials.get('consumer_key', '') if broker_choice == "Kotak Neo" else config['kotak_neo'].get('consumer_key', ''),
            'consumer_secret': broker_credentials.get('consumer_secret', '') if broker_choice == "Kotak Neo" else config['kotak_neo'].get('consumer_secret', '')
        },
        'trading': {
            'underlying_symbol': underlying,
            'exchange': exchange,
            'lot_size': lot_size,
            'max_loss_per_trade': max_loss,
            'dry_run': dry_run
        }
    }
    with open(config_path, 'w') as f:
        yaml.dump(new_config, f)
    st.sidebar.success("✅ Configuration saved!")

# Test Connection
st.sidebar.subheader("🔌 Connection")
if st.sidebar.button(f"Test {broker_choice} Connection"):
    with st.spinner(f"Connecting to {broker_choice}..."):
        try:
            if broker_choice == "Angel One":
                if not broker_credentials.get('api_key') or not broker_credentials.get('client_id') or not broker_credentials.get('password'):
                    st.sidebar.error("❌ Please fill in all credentials")
                elif broker_credentials.get('api_key', '').startswith("DEMO_"):
                    st.sidebar.warning("⚠️ Using demo credentials - cannot connect to real broker")
                else:
                    st.info(f"🔍 Testing with Client ID: {broker_credentials.get('client_id')}")
                    st.info(f"🔍 API Key length: {len(broker_credentials.get('api_key', ''))} chars")
                    st.info(f"🔍 TOTP Secret: {'Set' if broker_credentials.get('totp_secret') else 'Not set'}")
                    
                    broker = AngelOneClient(
                        broker_credentials.get('api_key'),
                        broker_credentials.get('client_id'),
                        broker_credentials.get('password'),
                        broker_credentials.get('totp_secret') if broker_credentials.get('totp_secret') else None
                    )
                    login_result = broker.login()
                    
                    if login_result:
                        st.sidebar.success("✅ Connected to Angel One!")
                        st.session_state.broker_connected = True
                    else:
                        st.sidebar.error("❌ Connection failed")
                        st.error("Possible issues:")
                        st.error("1. Verify API Key from https://smartapi.angelbroking.com/")
                        st.error("2. Check Client ID (your Angel One login)")
                        st.error("3. Verify password is correct")
                        st.error("4. If using TOTP, check the secret key")
                        st.session_state.broker_connected = False
            else:  # Kotak Neo
                if not all([broker_credentials.get('api_key'), broker_credentials.get('user_id'), 
                           broker_credentials.get('password'), broker_credentials.get('consumer_key'),
                           broker_credentials.get('consumer_secret')]):
                    st.sidebar.error("❌ Please fill in all credentials")
                else:
                    st.info(f"🔍 Testing with User ID: {broker_credentials.get('user_id')}")
                    st.info(f"🔍 API Key length: {len(broker_credentials.get('api_key', ''))} chars")
                    
                    broker = KotakNeoClient(
                        broker_credentials.get('api_key'),
                        broker_credentials.get('user_id'),
                        broker_credentials.get('password'),
                        broker_credentials.get('consumer_key'),
                        broker_credentials.get('consumer_secret')
                    )
                    login_result = broker.login()
                    
                    if login_result:
                        st.sidebar.success("✅ Connected to Kotak Neo!")
                        st.session_state.broker_connected = True
                    else:
                        st.sidebar.error("❌ Connection failed")
                        st.error("Possible issues:")
                        st.error("1. Verify API Key and credentials")
                        st.error("2. Check Consumer Key and Consumer Secret")
                        st.error("3. Verify user ID and password")
                        st.session_state.broker_connected = False
        except Exception as e:
            st.sidebar.error(f"❌ Error: {str(e)}")
            st.error(f"Full error: {repr(e)}")
            st.session_state.broker_connected = False

# Main content
st.title("📈 Non-Directional Strangle Trading Bot")
st.markdown("---")

# Status row
col1, col2, col3, col4 = st.columns(4)

with col1:
    status = "🟢 RUNNING" if st.session_state.bot_running else "🔴 STOPPED"
    st.metric("Bot Status", status)

with col2:
    mode = "🧪 DRY RUN" if dry_run else "⚡ LIVE TRADING"
    st.metric("Mode", mode)

with col3:
    conn_status = "✅ Connected" if st.session_state.broker_connected else "⚠️ Not Connected"
    st.metric("Broker", conn_status)

with col4:
    st.metric("Active Signals", len(st.session_state.signals))

st.markdown("---")

# Control buttons
col_start, col_stop = st.columns(2)

with col_start:
    if st.button("▶️ START BOT", disabled=st.session_state.bot_running, use_container_width=True):
        required_fields = {
            'Angel One': ['api_key', 'client_id', 'password'],
            'Kotak Neo': ['api_key', 'user_id', 'password', 'consumer_key', 'consumer_secret']
        }
        if not all(broker_credentials.get(field) for field in required_fields[broker_choice]):
            st.error(f"❌ Please configure {broker_choice} credentials first")
        else:
            st.session_state.bot_running = True
            st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Bot started with {broker_choice}")
            st.rerun()

with col_stop:
    if st.button("⏹️ STOP BOT", disabled=not st.session_state.bot_running, use_container_width=True):
        st.session_state.bot_running = False
        st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Bot stopped")
        st.rerun()

st.markdown("---")

# Tabs for different views
tab1, tab2, tab3, tab4 = st.tabs(["📊 Signals", "💼 Positions", "📈 Charts", "📝 Logs"])

with tab1:
    st.subheader("Recent Signals")
    if st.session_state.signals:
        signals_df = pd.DataFrame([
            {
                'Time': s.timestamp,
                'Action': s.action,
                'Reason': s.context.get('reason', ''),
                'Call Distance': s.call_distance,
                'Put Distance': s.put_distance,
                'Situation': s.context.get('situation', '')
            }
            for s in st.session_state.signals
        ])
        st.dataframe(signals_df, use_container_width=True)
    else:
        st.info("No signals yet. Upload data or wait for live signals.")

with tab2:
    st.subheader("Active Positions")
    if st.session_state.positions:
        positions_df = pd.DataFrame(st.session_state.positions)
        st.dataframe(positions_df, use_container_width=True)
    else:
        st.info("No active positions")

with tab3:
    st.subheader("Price & OI Charts")
    st.info("Charts will appear when data is loaded")
    
    # Placeholder for charts
    if False:  # Will enable when data is available
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=[], open=[], high=[], low=[], close=[]))
        fig.update_layout(title="Price Action", xaxis_title="Time", yaxis_title="Price")
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("Activity Logs")
    if st.session_state.logs:
        for log in reversed(st.session_state.logs[-50:]):  # Show last 50 logs
            st.text(log)
    else:
        st.info("No logs yet")

# Data Upload Section
st.markdown("---")
st.subheader("📁 Upload Market Data")

col_upload1, col_upload2, col_upload3 = st.columns(3)

with col_upload1:
    candles_file = st.file_uploader("Candles CSV", type=['csv'], key="candles")
    
with col_upload2:
    oi_file = st.file_uploader("OI Data CSV", type=['csv'], key="oi")
    
with col_upload3:
    futures_file = st.file_uploader("Futures OI CSV", type=['csv'], key="futures")

if st.button("🔄 Process Data", disabled=not (candles_file and oi_file and futures_file)):
    with st.spinner("Processing data..."):
        try:
            # Load data
            candles_df = pd.read_csv(candles_file)
            oi_df = pd.read_csv(oi_file)
            futures_df = pd.read_csv(futures_file)
            
            # Convert to model objects
            candles = [
                Candle(str(r.timestamp), float(r.open), float(r.high), float(r.low), float(r.close))
                for r in candles_df.itertuples(index=False)
            ]
            oi = [
                OIData(str(r.timestamp), float(r.oi_call_atm), float(r.oi_put_atm))
                for r in oi_df.itertuples(index=False)
            ]
            fut = [
                FuturesOI(str(r.timestamp), float(r.current_month_oi), float(r.next_month_oi))
                for r in futures_df.itertuples(index=False)
            ]
            
            # Run strategy
            strategy = NonDirectionalStrangleStrategy()
            new_signals = []
            
            for i in range(4, min(len(candles), len(oi), len(fut)) + 1):
                sig = strategy.evaluate(candles[:i], oi[:i], fut[:i])
                if sig:
                    new_signals.append(sig)
                    st.session_state.signals.append(sig)
            
            st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Processed {len(candles)} candles, found {len(new_signals)} signals")
            st.success(f"✅ Found {len(new_signals)} signals")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error processing data: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <small>
    ⚠️ <b>Risk Warning:</b> Options trading involves substantial risk. 
    Always test in dry-run mode first. Use at your own risk.
    </small>
</div>
""", unsafe_allow_html=True)

# Auto-refresh when bot is running
if st.session_state.bot_running:
    time.sleep(2)
    st.rerun()
