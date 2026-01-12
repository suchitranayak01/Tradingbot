"""
Streamlit page for Trending Stocks Screener
Identifies stocks with strong trends and high volume
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.screener.trending_screener import TrendingStockScreener, IntraDayScreener


def fetch_stock_data(symbol: str) -> dict:
    """Fetch stock data - mock implementation for demo."""
    # In production, use yfinance or your broker API
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1mo")
        info = ticker.info
        
        if hist.empty:
            return None
        
        current_price = hist['Close'].iloc[-1]
        current_volume = hist['Volume'].iloc[-1]
        avg_volume = hist['Volume'].mean()
        price_change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
        
        return {
            'symbol': symbol,
            'price': current_price,
            'volume': current_volume,
            'avg_volume': avg_volume,
            'price_change': price_change,
        }
    except:
        return None


def main():
    st.set_page_config(page_title="Trending Stocks Screener", layout="wide", initial_sidebar_state="expanded")
    
    st.title("📈 Trending Stocks Screener")
    st.markdown("Identify high-momentum stocks with above-average volume for intraday trading")
    
    # Sidebar Configuration
    st.sidebar.header("⚙️ Screener Settings")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        min_volume_increase = st.number_input(
            "Min Volume Increase %",
            min_value=10,
            max_value=500,
            value=50,
            help="Volume must exceed average by this %"
        )
    
    with col2:
        min_price_change = st.number_input(
            "Min Price Change %",
            min_value=0.5,
            max_value=20.0,
            value=2.0,
            step=0.5,
            help="Stock must move at least this much"
        )
    
    min_avg_volume = st.sidebar.number_input(
        "Min Average Volume",
        min_value=10000,
        max_value=10000000,
        value=100000,
        step=50000,
        help="Daily average volume requirement"
    )
    
    # Initialize screener
    screener = TrendingStockScreener(
        min_volume_increase_pct=min_volume_increase,
        min_price_change_pct=min_price_change,
        min_avg_volume=min_avg_volume,
    )
    
    intraday_screener = IntraDayScreener(
        min_volume_increase=min_volume_increase,
        target_price_change=min_price_change * 1.5,
    )
    
    # Input section
    st.sidebar.header("📊 Input Data")
    input_method = st.sidebar.radio("How to input stocks?", ["Manual Entry", "CSV Upload"])
    
    stocks_data = []
    
    if input_method == "Manual Entry":
        st.sidebar.markdown("### Add Stocks")
        symbol = st.sidebar.text_input("Stock Symbol", value="RELIANCE").upper()
        price = st.sidebar.number_input("Current Price", value=3000.0, step=10.0)
        volume = st.sidebar.number_input("Current Volume", value=500000, step=10000)
        avg_volume = st.sidebar.number_input("Avg Volume (20 days)", value=300000, step=10000)
        price_change = st.sidebar.number_input("Price Change %", value=2.5, step=0.1)
        
        if st.sidebar.button("Add Stock", key="add_stock"):
            stocks_data.append({
                'symbol': symbol,
                'price': price,
                'volume': volume,
                'avg_volume': avg_volume,
                'price_change': price_change,
            })
    
    else:  # CSV Upload
        uploaded_file = st.sidebar.file_uploader("Upload CSV", type=['csv'])
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            # Expected columns: symbol, price, volume, avg_volume, price_change
            for _, row in df.iterrows():
                stocks_data.append(row.to_dict())
    
    # Demo stocks if no data
    if not stocks_data:
        st.info("📝 Add stocks to screen them. Here are sample stocks:")
        demo_stocks = [
            {'symbol': 'RELIANCE', 'price': 3050, 'volume': 5000000, 'avg_volume': 3000000, 'price_change': 2.5},
            {'symbol': 'TCS', 'price': 4200, 'volume': 2500000, 'avg_volume': 1500000, 'price_change': 1.8},
            {'symbol': 'INFY', 'price': 1800, 'volume': 3000000, 'avg_volume': 2000000, 'price_change': 3.2},
            {'symbol': 'WIPRO', 'price': 450, 'volume': 4500000, 'avg_volume': 2500000, 'price_change': 2.1},
            {'symbol': 'HDFC', 'price': 2700, 'volume': 2000000, 'avg_volume': 1200000, 'price_change': 1.5},
        ]
        stocks_data = demo_stocks
    
    if stocks_data:
        # Screen stocks
        screening_results = []
        for stock in stocks_data:
            result = screener.screen_stock(
                symbol=stock['symbol'],
                current_price=stock['price'],
                current_volume=stock['volume'],
                avg_volume=stock['avg_volume'],
                price_change_pct=stock['price_change'],
            )
            screening_results.append(result)
        
        # Display results in tabs
        tab1, tab2, tab3 = st.tabs(["🎯 Trending Stocks", "🚀 Intraday Opportunities", "📊 Detailed Analysis"])
        
        with tab1:
            st.subheader("Trending Stocks Ranked by Score")
            
            df_results = screener.rank_stocks(screening_results)
            
            if not df_results.empty:
                # Filter qualifying stocks
                df_qualified = df_results[df_results['qualifies']].copy()
                
                if not df_qualified.empty:
                    # Display metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Screened", len(df_results))
                    with col2:
                        st.metric("Qualified", len(df_qualified))
                    with col3:
                        st.metric("Success Rate", f"{len(df_qualified)/len(df_results)*100:.1f}%")
                    with col4:
                        st.metric("Avg Score", f"{df_qualified['screening_score'].mean():.1f}")
                    
                    st.markdown("---")
                    
                    # Display table
                    display_cols = ['symbol', 'price', 'price_change_pct', 'trend_direction', 
                                   'volume_increase_pct', 'trend_score', 'screening_score']
                    
                    df_display = df_qualified[display_cols].copy()
                    df_display.columns = ['Symbol', 'Price', 'Change %', 'Direction', 'Vol Increase %', 'Trend Score', 'Score']
                    
                    # Format columns
                    df_display['Price'] = df_display['Price'].apply(lambda x: f"₹{x:.2f}")
                    df_display['Change %'] = df_display['Change %'].apply(lambda x: f"{x:+.2f}%")
                    df_display['Vol Increase %'] = df_display['Vol Increase %'].apply(lambda x: f"{x:.1f}%")
                    df_display['Trend Score'] = df_display['Trend Score'].apply(lambda x: f"{x:.1f}")
                    df_display['Score'] = df_display['Score'].apply(lambda x: f"{x:.0f}")
                    
                    st.dataframe(df_display, use_container_width=True)
                    
                    # Download button
                    csv = df_qualified[display_cols].to_csv(index=False)
                    st.download_button(
                        label="Download Results (CSV)",
                        data=csv,
                        file_name=f"trending_stocks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No stocks met the criteria. Try adjusting the settings.")
            else:
                st.error("No data to display")
        
        with tab2:
            st.subheader("Intraday Trading Opportunities")
            
            df_intraday = intraday_screener.get_intraday_opportunities(screening_results)
            
            if not df_intraday.empty:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Intraday Opportunities", len(df_intraday))
                with col2:
                    st.metric("Avg Intraday Score", f"{df_intraday['intraday_score'].mean():.1f}")
                
                st.markdown("---")
                
                # Display intraday stocks
                display_cols = ['symbol', 'price', 'price_change_pct', 'volume_increase_pct', 'intraday_score']
                df_display = df_intraday[display_cols].copy()
                df_display.columns = ['Symbol', 'Price', 'Change %', 'Vol Increase %', 'Score']
                
                df_display['Price'] = df_display['Price'].apply(lambda x: f"₹{x:.2f}")
                df_display['Change %'] = df_display['Change %'].apply(lambda x: f"{x:+.2f}%")
                df_display['Vol Increase %'] = df_display['Vol Increase %'].apply(lambda x: f"{x:.1f}%")
                df_display['Score'] = df_display['Score'].apply(lambda x: f"{x:.1f}")
                
                st.dataframe(df_display, use_container_width=True)
            else:
                st.info("No intraday opportunities found with current settings")
        
        with tab3:
            st.subheader("Detailed Stock Analysis")
            
            # Select stock for detailed view
            stock_symbols = [s['symbol'] for s in screening_results]
            selected_symbol = st.selectbox("Select Stock", stock_symbols)
            
            if selected_symbol:
                stock_data = next((s for s in screening_results if s['symbol'] == selected_symbol), None)
                
                if stock_data:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Price", f"₹{stock_data['price']:.2f}")
                    with col2:
                        st.metric("Change", f"{stock_data['price_change_pct']:+.2f}%")
                    with col3:
                        st.metric("Trend Score", f"{stock_data['trend_score']:.1f}")
                    
                    st.markdown("---")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### Volume Analysis")
                        vol_metrics = {
                            'Current Volume': f"{stock_data['current_volume']:,}",
                            'Avg Volume': f"{stock_data['avg_volume']:,}",
                            'Volume Increase': f"{stock_data['volume_increase_pct']:.1f}%",
                        }
                        for metric, value in vol_metrics.items():
                            st.write(f"**{metric}:** {value}")
                    
                    with col2:
                        st.markdown("### Screening Criteria")
                        criteria = {
                            'Volume Criteria Met': "✅" if stock_data['meets_volume_criteria'] else "❌",
                            'Price Change Met': "✅" if stock_data['meets_price_criteria'] else "❌",
                            'Qualifies': "✅ YES" if stock_data['qualifies'] else "❌ NO",
                            'Screening Score': f"{stock_data['screening_score']:.0f}/100",
                        }
                        for criterion, status in criteria.items():
                            st.write(f"**{criterion}:** {status}")


# Call main function directly for Streamlit multi-page apps
main()
