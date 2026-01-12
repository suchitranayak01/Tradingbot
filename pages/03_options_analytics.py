"""
Streamlit page for Options Analytics
Display Straddle charts, VIX, IV, and PCR analysis
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.screener.options_analyzer import StraddleAnalyzer, ImpliedVolatilityAnalyzer, PutCallRatioAnalyzer, VIXAnalyzer


def main():
    st.set_page_config(page_title="Options Analytics", layout="wide", initial_sidebar_state="expanded")
    
    st.title("📊 Options Analytics & Straddle Strategy")
    st.markdown("Analyze straddles, implied volatility, PCR, and VIX for options trading")
    
    # Sidebar Configuration
    st.sidebar.header("⚙️ Options Data Input")
    
    # Underlying and Strike Selection
    underlying_price = st.sidebar.number_input(
        "Underlying Price",
        min_value=1.0,
        value=23000.0,
        step=100.0,
        help="Current spot price (e.g., NIFTY 50)"
    )
    
    strike_distance = st.sidebar.selectbox(
        "Strike Distance",
        [50, 100, 200, 500],
        index=1,
        help="Standard strike intervals"
    )
    
    # ATM Straddle Inputs
    st.sidebar.markdown("### ATM Straddle")
    atm_call_price = st.sidebar.number_input(
        "ATM Call Premium",
        min_value=0.0,
        value=450.0,
        step=10.0,
        help="Premium for ATM call option"
    )
    
    atm_put_price = st.sidebar.number_input(
        "ATM Put Premium",
        min_value=0.0,
        value=480.0,
        step=10.0,
        help="Premium for ATM put option"
    )
    
    # Implied Volatility
    st.sidebar.markdown("### Implied Volatility")
    call_iv = st.sidebar.slider(
        "Call IV %",
        min_value=0.0,
        max_value=100.0,
        value=18.5,
        step=0.5
    )
    
    put_iv = st.sidebar.slider(
        "Put IV %",
        min_value=0.0,
        max_value=100.0,
        value=19.2,
        step=0.5
    )
    
    # VIX and PCR
    st.sidebar.markdown("### Market Metrics")
    vix = st.sidebar.number_input(
        "VIX Level",
        min_value=0.0,
        value=16.5,
        step=0.1,
        help="Volatility Index"
    )
    
    put_volume = st.sidebar.number_input(
        "Total Put Volume",
        min_value=0,
        value=500000,
        step=10000
    )
    
    call_volume = st.sidebar.number_input(
        "Total Call Volume",
        min_value=1,
        value=350000,
        step=10000
    )
    
    put_oi = st.sidebar.number_input(
        "Put OI",
        min_value=0,
        value=2500000,
        step=100000
    )
    
    call_oi = st.sidebar.number_input(
        "Call OI",
        min_value=1,
        value=2000000,
        step=100000
    )
    
    # Term structure
    st.sidebar.markdown("### IV Term Structure")
    near_month_iv = st.sidebar.slider("Near Month IV %", 0.0, 100.0, call_iv, 0.5)
    far_month_iv = st.sidebar.slider("Far Month IV %", 0.0, 100.0, call_iv + 1, 0.5)
    
    # Initialize analyzers
    straddle_analyzer = StraddleAnalyzer(underlying_price, strike_distance)
    iv_analyzer = ImpliedVolatilityAnalyzer()
    pcr_analyzer = PutCallRatioAnalyzer()
    vix_analyzer = VIXAnalyzer()
    
    # Perform analyses
    straddle_analysis = straddle_analyzer.analyze_straddle(atm_call_price, atm_put_price, call_iv, put_iv)
    pcr_analysis = pcr_analyzer.calculate_pcr(put_volume, call_volume, put_oi, call_oi)
    iv_term = iv_analyzer.iv_term_structure(near_month_iv, far_month_iv)
    vix_interp = vix_analyzer.interpret_vix_level(vix)
    
    # Display results in tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Straddle", "🎯 IV Analysis", "📊 PCR", "📈 VIX", "💡 Insights"])
    
    with tab1:
        st.subheader("ATM Straddle Analysis")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("ATM Strike", f"{straddle_analysis['atm_strike']:.0f}")
        with col2:
            st.metric("Straddle Cost", f"₹{straddle_analysis['straddle_price']:.0f}")
        with col3:
            st.metric("Avg IV", f"{straddle_analysis['avg_iv']:.2f}%")
        with col4:
            st.metric("Expected Daily Move", f"₹{straddle_analysis['expected_daily_move']:.0f}")
        
        st.markdown("---")
        
        # Straddle breakdown
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Option Prices")
            option_data = {
                'Component': ['ATM Call', 'ATM Put', 'Total Straddle'],
                'Premium': [
                    f"₹{atm_call_price:.0f}",
                    f"₹{atm_put_price:.0f}",
                    f"₹{straddle_analysis['straddle_price']:.0f}"
                ],
                'IV': [
                    f"{call_iv:.2f}%",
                    f"{put_iv:.2f}%",
                    f"{straddle_analysis['avg_iv']:.2f}%"
                ]
            }
            st.dataframe(pd.DataFrame(option_data), use_container_width=True)
        
        with col2:
            st.markdown("### Breakeven Points")
            be_data = {
                'Level': ['Lower Breakeven', 'ATM Strike', 'Upper Breakeven'],
                'Price': [
                    f"₹{straddle_analysis['lower_breakeven']:.0f}",
                    f"₹{straddle_analysis['atm_strike']:.0f}",
                    f"₹{straddle_analysis['upper_breakeven']:.0f}"
                ],
                'Distance from ATM': [
                    f"₹{straddle_analysis['lower_breakeven'] - straddle_analysis['atm_strike']:.0f}",
                    "0",
                    f"₹{straddle_analysis['upper_breakeven'] - straddle_analysis['atm_strike']:.0f}"
                ]
            }
            st.dataframe(pd.DataFrame(be_data), use_container_width=True)
        
        st.markdown("---")
        
        # Straddle payoff chart
        st.markdown("### Straddle Payoff Diagram")
        
        atm = straddle_analysis['atm_strike']
        spot_range = np.linspace(atm - 500, atm + 500, 100)
        payoff_df = straddle_analyzer.calculate_straddle_payoff(
            spot_range,
            straddle_analysis['atm_strike'],
            straddle_analysis['straddle_price']
        )
        
        fig = go.Figure()
        
        # Add payoff line
        fig.add_trace(go.Scatter(
            x=payoff_df['spot'],
            y=payoff_df['pnl'],
            mode='lines',
            name='Straddle P&L',
            line=dict(color='blue', width=3)
        ))
        
        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Breakeven")
        
        # Add breakeven lines
        fig.add_vline(x=straddle_analysis['lower_breakeven'], line_dash="dot", line_color="orange")
        fig.add_vline(x=straddle_analysis['upper_breakeven'], line_dash="dot", line_color="orange")
        
        # Add current spot
        fig.add_vline(x=underlying_price, line_dash="dash", line_color="green", annotation_text="Current Spot")
        
        fig.update_layout(
            title="Straddle P&L at Expiry",
            xaxis_title="Spot Price (₹)",
            yaxis_title="Profit/Loss (₹)",
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Implied Volatility Analysis")
        
        # IV metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Call IV", f"{call_iv:.2f}%")
        with col2:
            st.metric("Put IV", f"{put_iv:.2f}%")
        with col3:
            st.metric("IV Spread", f"{abs(call_iv - put_iv):.2f}%")
        with col4:
            iv_skew = abs(call_iv - put_iv)
            st.metric("Call/Put IV Ratio", f"{call_iv/put_iv if put_iv > 0 else 0:.3f}")
        
        st.markdown("---")
        
        # Term structure
        st.markdown("### IV Term Structure")
        col1, col2 = st.columns(2)
        
        with col1:
            ts_data = {
                'Expiry': ['Near Month', 'Far Month'],
                'IV %': [f"{near_month_iv:.2f}", f"{far_month_iv:.2f}"],
                'Structure': [
                    'Front Month',
                    'Back Month'
                ]
            }
            st.dataframe(pd.DataFrame(ts_data), use_container_width=True)
            
            st.markdown(f"**Structure:** {iv_term['structure']}")
            st.markdown(f"**IV Slope:** {iv_term['iv_slope_pct']:.2f}%")
            st.info(iv_term['interpretation'])
        
        with col2:
            # IV term structure chart
            terms = ['Near\nMonth', 'Far\nMonth']
            ivs = [near_month_iv, far_month_iv]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=terms,
                y=ivs,
                mode='lines+markers',
                line=dict(color='purple', width=3),
                marker=dict(size=12)
            ))
            
            fig.update_layout(
                title="IV Term Structure",
                yaxis_title="Implied Volatility %",
                hovermode='x unified',
                height=300
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("Put-Call Ratio (PCR) Analysis")
        
        # PCR metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            volume_pcr = pcr_analysis.get('volume_pcr', 0)
            st.metric("Volume PCR", f"{volume_pcr:.3f}")
            st.caption(f"Sentiment: {pcr_analyzer.sentiment_from_pcr(volume_pcr)}")
        
        with col2:
            oi_pcr = pcr_analysis.get('oi_pcr', 0)
            st.metric("OI PCR", f"{oi_pcr:.3f}")
            st.caption(f"Sentiment: {pcr_analyzer.sentiment_from_pcr(oi_pcr)}")
        
        with col3:
            st.metric("Put Volume", f"{put_volume:,}")
        
        with col4:
            st.metric("Call Volume", f"{call_volume:,}")
        
        st.markdown("---")
        
        # PCR interpretation
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Volume PCR")
            vol_interp = pcr_analysis.get('volume_pcr_interpretation', 'Neutral')
            if vol_interp == "Bullish":
                st.success(f"📈 {vol_interp} - More calls bought, market expects upside")
            elif vol_interp == "Bearish":
                st.error(f"📉 {vol_interp} - More puts bought, market expects downside")
            else:
                st.info(f"➡️ {vol_interp} - Balanced put-call activity")
        
        with col2:
            st.markdown("### OI PCR")
            oi_interp = pcr_analysis.get('oi_pcr_interpretation', 'Neutral')
            if oi_interp == "Bullish":
                st.success(f"📈 {oi_interp} - Call OI dominance")
            elif oi_interp == "Bearish":
                st.error(f"📉 {oi_interp} - Put OI dominance")
            else:
                st.info(f"➡️ {oi_interp} - Balanced OI")
        
        st.markdown("---")
        
        # PCR comparison chart
        st.markdown("### PCR Comparison")
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=['Volume PCR', 'OI PCR'],
            y=[pcr_analysis.get('volume_pcr', 0), pcr_analysis.get('oi_pcr', 0)],
            marker_color=['lightblue', 'lightcoral']
        ))
        
        fig.add_hline(y=1.0, line_dash="dash", line_color="green", annotation_text="Neutral (1.0)")
        
        fig.update_layout(
            title="Put-Call Ratio Comparison",
            yaxis_title="PCR Value",
            hovermode='x unified',
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.subheader("VIX (Volatility Index) Analysis")
        
        # VIX metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("VIX Level", f"{vix:.2f}")
        
        with col2:
            st.metric("Category", vix_interp['vix_category'])
        
        with col3:
            st.metric("Market State", vix_interp['market_state'])
        
        with col4:
            # VIX gauge
            if vix < 12:
                status = "🟢 Low"
            elif vix < 20:
                status = "🟡 Moderate"
            else:
                status = "🔴 High"
            st.metric("Status", status)
        
        st.markdown("---")
        
        # VIX interpretation
        st.markdown("### Market Implication")
        st.info(vix_interp['implication'])
        
        st.markdown("---")
        
        # VIX level chart
        st.markdown("### VIX Levels & Zones")
        
        vix_zones = {
            'Zone': ['Complacent', 'Normal', 'Nervous', 'Panicked'],
            'VIX Range': ['<12', '12-16', '16-30', '>30'],
            'Market State': ['Very Low Vol', 'Calm', 'High Vol', 'Crisis'],
            'Strategy': ['Sell Vol', 'Balanced', 'Buy Vol', 'Risk Off']
        }
        
        st.dataframe(pd.DataFrame(vix_zones), use_container_width=True)
    
    with tab5:
        st.subheader("💡 Trading Insights")
        
        st.markdown("### Straddle Strategy Recommendation")
        
        # Determine if straddle is worth selling
        expected_move = straddle_analysis['expected_daily_move']
        straddle_cost = straddle_analysis['straddle_price']
        
        if expected_move > straddle_cost:
            st.warning(
                f"""
                ⚠️ **Expected Move (₹{expected_move:.0f}) > Straddle Cost (₹{straddle_cost:.0f})**
                
                Market might move more than what the option sellers are pricing in.
                **AVOID selling straddle** - Higher risk than premium collected.
                """
            )
        else:
            st.success(
                f"""
                ✅ **Expected Move (₹{expected_move:.0f}) < Straddle Cost (₹{straddle_cost:.0f})**
                
                Option sellers are pricing good premium.
                **GOOD environment to SELL straddle** - Premium collection likely to exceed moves.
                """
            )
        
        st.markdown("---")
        
        st.markdown("### Market Sentiment Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### Volatility View")
            if vix < 16:
                st.info("📉 Low volatility - Market is calm")
            elif vix > 25:
                st.error("📈 High volatility - Market is nervous")
            else:
                st.warning("⚖️ Normal volatility - Balanced conditions")
        
        with col2:
            st.markdown("#### Direction View")
            volume_pcr = pcr_analysis.get('volume_pcr', 1)
            if volume_pcr < 0.8:
                st.success("📈 Bullish - More calls bought")
            elif volume_pcr > 1.2:
                st.error("📉 Bearish - More puts bought")
            else:
                st.info("➡️ Neutral - Balanced outlook")
        
        with col3:
            st.markdown("#### Volatility Structure")
            if iv_term['structure'] == 'Contango':
                st.info("📈 Contango - IV rising (buy near, sell far)")
            else:
                st.warning("📉 Backwardation - IV declining (sell near, buy far)")
        
        st.markdown("---")
        
        st.markdown("### Recommended Strategies")
        
        strategies = []
        
        # Straddle recommendation
        if expected_move < straddle_cost:
            strategies.append("✅ Sell Straddle - Good premium environment")
        else:
            strategies.append("❌ Avoid Selling Straddle - Expected move too high")
        
        # VIX based
        if vix > 25:
            strategies.append("📈 Buy Straddle/Strangle - Volatility likely to calm down (sell off later)")
        elif vix < 12:
            strategies.append("⚠️ Be careful with volatility spikes - Consider protective strategies")
        
        # PCR based
        if pcr_analysis.get('volume_pcr', 1) < 0.8:
            strategies.append("📈 Bullish Strategies - Calls are favored")
        elif pcr_analysis.get('volume_pcr', 1) > 1.2:
            strategies.append("📉 Bearish Strategies - Puts are favored")
        
        for strategy in strategies:
            st.markdown(f"• {strategy}")


if __name__ == "__main__":
    main()
