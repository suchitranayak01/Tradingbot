"""
Streamlit page for All-Time High (ATH) Stock Screener
Identifies stocks trading near all-time highs
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.screener.ath_screener import ATHStockScreener, ConsistentHighPerformer


def main():
    st.set_page_config(page_title="ATH Stocks Screener", layout="wide", initial_sidebar_state="expanded")
    
    st.title("🔝 All-Time High (ATH) Stocks Screener")
    st.markdown("Find stocks trading near or at their all-time highs with strong volume")
    
    # Sidebar Configuration
    st.sidebar.header("⚙️ Screener Settings")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        ath_distance = st.number_input(
            "ATH Distance %",
            min_value=1,
            max_value=20,
            value=5,
            help="Stock must be within this % of ATH"
        )
    
    with col2:
        min_volume = st.number_input(
            "Min Volume",
            min_value=100000,
            max_value=10000000,
            value=500000,
            step=100000,
            help="Minimum daily volume"
        )
    
    min_price = st.sidebar.number_input(
        "Min Price Level",
        min_value=10.0,
        max_value=100000.0,
        value=100.0,
        step=10.0,
        help="Minimum stock price"
    )
    
    # Initialize screener
    screener = ATHStockScreener(
        ath_distance_pct=ath_distance,
        min_volume=min_volume,
        min_price=min_price,
    )
    
    # Input section
    st.sidebar.header("📊 Input Data")
    input_method = st.sidebar.radio("How to input stocks?", ["Manual Entry", "CSV Upload"])
    
    stocks_data = []
    
    if input_method == "Manual Entry":
        st.sidebar.markdown("### Add Stocks")
        symbol = st.sidebar.text_input("Stock Symbol", value="RELIANCE").upper()
        price = st.sidebar.number_input("Current Price", value=3000.0, step=10.0)
        ath = st.sidebar.number_input("All-Time High", value=3100.0, step=10.0)
        volume = st.sidebar.number_input("Current Volume", value=5000000, step=100000)
        avg_volume = st.sidebar.number_input("Avg Volume", value=3000000, step=100000)
        
        if st.sidebar.button("Add Stock", key="add_stock"):
            stocks_data.append({
                'symbol': symbol,
                'price': price,
                'ath': ath,
                'volume': volume,
                'avg_volume': avg_volume,
            })
    
    else:  # CSV Upload
        uploaded_file = st.sidebar.file_uploader("Upload CSV", type=['csv'])
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            # Expected columns: symbol, price, ath, volume, avg_volume
            for _, row in df.iterrows():
                stocks_data.append(row.to_dict())
    
    # Demo stocks if no data
    if not stocks_data:
        st.info("📝 Add stocks to screen them. Here are sample stocks near ATH:")
        demo_stocks = [
            {'symbol': 'RELIANCE', 'price': 3050, 'ath': 3100, 'volume': 5000000, 'avg_volume': 3000000},
            {'symbol': 'TCS', 'price': 4150, 'ath': 4200, 'volume': 2500000, 'avg_volume': 1500000},
            {'symbol': 'INFY', 'price': 1780, 'ath': 1850, 'volume': 3000000, 'avg_volume': 2000000},
            {'symbol': 'WIPRO', 'price': 445, 'ath': 460, 'volume': 4500000, 'avg_volume': 2500000},
            {'symbol': 'HDFC', 'price': 2690, 'ath': 2750, 'volume': 2000000, 'avg_volume': 1200000},
        ]
        stocks_data = demo_stocks
    
    if stocks_data:
        # Screen stocks
        screening_results = []
        for stock in stocks_data:
            result = screener.screen_stock(
                symbol=stock['symbol'],
                current_price=stock['price'],
                all_time_high=stock['ath'],
                current_volume=stock['volume'],
                avg_volume=stock['avg_volume'],
            )
            screening_results.append(result)
        
        # Display results in tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🎯 ATH Candidates", "🚀 Breakout Prospects", "📊 Detailed Analysis", "📈 Strength Ranking"])
        
        with tab1:
            st.subheader("Stocks Near All-Time High")
            
            df_results = screener.rank_stocks(screening_results)
            
            if not df_results.empty:
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Screened", len(screening_results))
                with col2:
                    st.metric("Near ATH", len(df_results))
                with col3:
                    st.metric("Success Rate", f"{len(df_results)/len(screening_results)*100:.1f}%")
                with col4:
                    avg_distance = df_results['distance_from_ath_pct'].mean()
                    st.metric("Avg Distance from ATH", f"{avg_distance:.2f}%")
                
                st.markdown("---")
                
                # Display table
                display_cols = ['symbol', 'current_price', 'all_time_high', 'distance_from_ath_pct', 
                               'volume_ratio', 'proximity_score', 'breakout_probability']
                
                df_display = df_results[display_cols].copy()
                df_display.columns = ['Symbol', 'Price', 'ATH', 'Distance %', 'Vol Ratio', 'Proximity', 'Breakout %']
                
                # Format columns
                df_display['Price'] = df_display['Price'].apply(lambda x: f"₹{x:.2f}")
                df_display['ATH'] = df_display['ATH'].apply(lambda x: f"₹{x:.2f}")
                df_display['Distance %'] = df_display['Distance %'].apply(lambda x: f"{x:.2f}%")
                df_display['Vol Ratio'] = df_display['Vol Ratio'].apply(lambda x: f"{x:.2f}x")
                df_display['Proximity'] = df_display['Proximity'].apply(lambda x: f"{x:.1f}")
                df_display['Breakout %'] = df_display['Breakout %'].apply(lambda x: f"{x*100:.1f}%")
                
                st.dataframe(df_display, use_container_width=True)
                
                # Download button
                csv = df_results[display_cols].to_csv(index=False)
                st.download_button(
                    label="Download Results (CSV)",
                    data=csv,
                    file_name=f"ath_stocks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No stocks near ATH found with current criteria")
        
        with tab2:
            st.subheader("Breakout Prospects (High Confidence)")
            
            df_breakout = pd.DataFrame([s for s in screening_results if s['qualifies']])
            df_breakout = df_breakout.sort_values('total_score', ascending=False)
            
            if not df_breakout.empty:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Breakout Candidates", len(df_breakout))
                with col2:
                    st.metric("Avg Breakout Score", f"{df_breakout['total_score'].mean():.1f}")
                
                st.markdown("---")
                
                display_cols = ['symbol', 'current_price', 'all_time_high', 'distance_from_ath_pct',
                               'proximity_score', 'momentum_score', 'total_score']
                
                df_display = df_breakout[display_cols].copy()
                df_display.columns = ['Symbol', 'Price', 'ATH', 'Dist %', 'Proximity', 'Momentum', 'Total']
                
                df_display['Price'] = df_display['Price'].apply(lambda x: f"₹{x:.2f}")
                df_display['ATH'] = df_display['ATH'].apply(lambda x: f"₹{x:.2f}")
                df_display['Dist %'] = df_display['Dist %'].apply(lambda x: f"{x:.2f}%")
                df_display['Proximity'] = df_display['Proximity'].apply(lambda x: f"{x:.1f}")
                df_display['Momentum'] = df_display['Momentum'].apply(lambda x: f"{x:.1f}")
                df_display['Total'] = df_display['Total'].apply(lambda x: f"{x:.1f}")
                
                st.dataframe(df_display, use_container_width=True)
            else:
                st.info("No high-confidence breakout candidates found")
        
        with tab3:
            st.subheader("Detailed Stock Analysis")
            
            stock_symbols = [s['symbol'] for s in screening_results]
            selected_symbol = st.selectbox("Select Stock", stock_symbols)
            
            if selected_symbol:
                stock_data = next((s for s in screening_results if s['symbol'] == selected_symbol), None)
                
                if stock_data:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Current Price", f"₹{stock_data['current_price']:.2f}")
                    with col2:
                        st.metric("All-Time High", f"₹{stock_data['all_time_high']:.2f}")
                    with col3:
                        st.metric("Distance from ATH", f"{stock_data['distance_from_ath_pct']:.2f}%")
                    
                    st.markdown("---")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### Price Analysis")
                        price_info = {
                            'Price Value': f"₹{stock_data['distance_from_ath_value']:.2f}",
                            'Distance %': f"{stock_data['distance_from_ath_pct']:.2f}%",
                            'ATH Rank': f"Top {(1 - stock_data['breakout_probability']) * 100:.1f}%",
                        }
                        for metric, value in price_info.items():
                            st.write(f"**{metric}:** {value}")
                    
                    with col2:
                        st.markdown("### Volume & Strength")
                        vol_info = {
                            'Current Volume': f"{stock_data['current_volume']:,}",
                            'Avg Volume': f"{stock_data['avg_volume']:,}",
                            'Volume Ratio': f"{stock_data['volume_ratio']:.2f}x",
                        }
                        for metric, value in vol_info.items():
                            st.write(f"**{metric}:** {value}")
                    
                    st.markdown("---")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Proximity Score", f"{stock_data['proximity_score']:.1f}")
                    with col2:
                        st.metric("Momentum Score", f"{stock_data['momentum_score']:.1f}")
                    with col3:
                        st.metric("Total Score", f"{stock_data['total_score']:.1f}/100")
                    
                    # Status
                    if stock_data['qualifies']:
                        st.success("✅ Stock qualifies for ATH screening")
                    else:
                        st.warning("⚠️ Stock does not meet criteria")
        
        with tab4:
            st.subheader("Stock Strength Ranking")
            
            df_strength = pd.DataFrame(screening_results)
            df_strength = df_strength.sort_values('total_score', ascending=False)
            
            # Create ranking visualization
            colors = []
            for score in df_strength['total_score']:
                if score >= 80:
                    colors.append('🟢')
                elif score >= 60:
                    colors.append('🟡')
                else:
                    colors.append('🔴')
            
            df_display = df_strength[['symbol', 'current_price', 'distance_from_ath_pct', 'total_score']].copy()
            df_display['Status'] = colors
            df_display.columns = ['Symbol', 'Price', 'Dist %', 'Score', 'Status']
            
            df_display['Price'] = df_display['Price'].apply(lambda x: f"₹{x:.2f}")
            df_display['Dist %'] = df_display['Dist %'].apply(lambda x: f"{x:.2f}%")
            df_display['Score'] = df_display['Score'].apply(lambda x: f"{x:.1f}")
            
            st.dataframe(df_display, use_container_width=True)
            
            # Summary
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                strong = len(df_strength[df_strength['total_score'] >= 80])
                st.info(f"🟢 Strong: {strong}")
            with col2:
                medium = len(df_strength[(df_strength['total_score'] >= 60) & (df_strength['total_score'] < 80)])
                st.warning(f"🟡 Medium: {medium}")
            with col3:
                weak = len(df_strength[df_strength['total_score'] < 60])
                st.error(f"🔴 Weak: {weak}")


# Call main function directly for Streamlit multi-page apps
main()
