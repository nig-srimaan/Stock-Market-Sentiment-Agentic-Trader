import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import json
import time  
import streamlit.components.v1 as components
from llm_engine import analyze_sentiment_batch
from scraper import fetch_financial_news
from smc_engine import generate_smc_signal

# --- IMPORT DEV 1's QUANT ENGINE ---
try:
    from smc_engine import generate_smc_signal
except ImportError:
    st.error("⚠️ Dev 2: Tell Dev 1 to save 'smc_engine.py' in the same folder!")

st.set_page_config(page_title="Agentic Stock Scanner", layout="wide")

if "news_df" not in st.session_state:
    st.session_state.news_df = pd.DataFrame()

POPULAR_STOCKS = [
    "NVDA - Nvidia Corp", "AAPL - Apple Inc", "MSFT - Microsoft", "TSLA - Tesla", 
    "AMZN - Amazon", "GOOGL - Alphabet (Google)", "META - Meta (Facebook)", "PLTR - Palantir",
    "SPY - S&P 500 Market Index", "QQQ - Nasdaq 100 Index", 
    "BTC-USD - Bitcoin", "ETH-USD - Ethereum", "SOL-USD - Solana",
    "RELIANCE.NS - Reliance Industries", "TCS.NS - Tata Consultancy Services", 
    "HDFCBANK.NS - HDFC Bank", "TATAMOTORS.NS - Tata Motors", "INFY.NS - Infosys"
]

st.title("⚡ Agentic Trading Terminal")

# --- AUTO BACKGROUND AI SCANNER ---
if st.session_state.news_df.empty:
    with st.spinner("🤖 System Booting: AI is analyzing global headlines..."):
        headlines = fetch_financial_news(count=50) 
        res = analyze_sentiment_batch(headlines)
        try:
            data = json.loads(res)
            if len(data) > 0:
                st.session_state.news_df = pd.DataFrame(data)
                st.rerun()
            else:
                st.error("Local AI returned empty data.")
        except Exception as e:
            st.error(f"Format error from Local AI: {e}")

# --- THE 4 MASTER TABS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Market Explorer", 
    "📰 AI Intelligence Feed", 
    "🤖 Autonomous Trading Agent",
    "📐 SMC Technical Analysis"
])

# ==========================================
# TAB 1: 1-SECOND TRADINGVIEW CHART
# ==========================================
with tab1:
    st.markdown("### 📈 Live Market Explorer (Tick-by-Tick)")
    selected_option = st.selectbox("Search for a Company, Ticker, or Crypto:", POPULAR_STOCKS)
    manual_ticker = selected_option.split(" - ")[0].strip()
    
    tv_ticker = manual_ticker
    if ".NS" in manual_ticker: tv_ticker = "NSE:" + manual_ticker.replace(".NS", "")
    elif "-" in manual_ticker: tv_ticker = "CRYPTO:" + manual_ticker.replace("-", "")
    else: tv_ticker = "NASDAQ:" + manual_ticker
    
    if manual_ticker:
        # 🚀 THE 1-SECOND TICK CHART: Native TradingView Widget!
        html_code = f"""
        <div class="tradingview-widget-container" style="height:600px;width:100%">
          <div id="tradingview_widget" style="height:100%;width:100%"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget(
          {{
          "autosize": true,
          "symbol": "{tv_ticker}",
          "interval": "1",
          "timezone": "exchange",
          "theme": "dark",
          "style": "1",
          "locale": "en",
          "enable_publishing": false,
          "backgroundColor": "#0E1117",
          "hide_top_toolbar": false,
          "save_image": false,
          "container_id": "tradingview_widget"
        }}
          );
          </script>
        </div>
        """
        
        # Render the live widget directly inside Streamlit (Set height to 600 here too!)
        components.html(html_code, height=600)

# ==========================================
# TAB 2: AI NEWS & PRICE TARGETS
# ==========================================
with tab2:
    if not st.session_state.news_df.empty:
        df = st.session_state.news_df
        st.markdown("### 📡 Live AI Intelligence Feed")
        display_df = df[['ticker', 'sentiment', 'confidence', 'headline', 'reasoning']].copy()
        display_df.columns = ['Ticker', 'Trend', 'Confidence (%)', 'Headline', 'AI Logic']
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("### 🎯 Deep Dive Analysis")
        selected_headline = st.selectbox("Select a breaking news story to chart:", df['headline'].tolist())
        selected_data = df[df['headline'] == selected_headline].iloc[0]
        
        target_ticker = str(selected_data.get('ticker', 'SPY')).upper()
        if target_ticker in ['NONE', 'NAN', '']: target_ticker = 'SPY'
        target_sentiment = str(selected_data.get('sentiment', 'Neutral')).capitalize()
        target_reasoning = str(selected_data.get('reasoning', 'Awaiting catalysts.'))
        try: target_confidence = int(selected_data.get('confidence', 50))
        except: target_confidence = 50
        
        colA, colB = st.columns([3, 1])
        
        with colB:
            st.subheader(f"🤖 Verdict & Targets")
            st.markdown(f"**Ticker Extracted:** `{target_ticker}`")
            if target_sentiment == 'Bullish': st.success(f"**Bias:** {target_sentiment} ({target_confidence}%)")
            elif target_sentiment == 'Bearish': st.error(f"**Bias:** {target_sentiment} ({target_confidence}%)")
            else: st.info(f"**Bias:** {target_sentiment} ({target_confidence}%)")
            st.markdown(f"**Logic:** *{target_reasoning}*")
            
            st.markdown("---")
            st.markdown("🎯 **AI Price Projection**")
            try:
                ai_chart_data = yf.download(target_ticker, period="1d", interval="1m")
                current_price = ai_chart_data['Close'].iloc[-1]
                move_percentage = 0.005 + (target_confidence / 100) * 0.025
                
                prefix = "₹" if ".NS" in target_ticker else "$"
                if target_sentiment == 'Bullish':
                    target_price = current_price * (1 + move_percentage)
                    st.metric(label="Current Price", value=f"{prefix}{current_price:.2f}")
                    st.metric(label="Expected Target", value=f"{prefix}{target_price:.2f}", delta=f"+{move_percentage*100:.1f}%")
                elif target_sentiment == 'Bearish':
                    target_price = current_price * (1 - move_percentage)
                    st.metric(label="Current Price", value=f"{prefix}{current_price:.2f}")
                    st.metric(label="Expected Target", value=f"{prefix}{target_price:.2f}", delta=f"-{move_percentage*100:.1f}%")
                else:
                    st.metric(label="Current Price", value=f"{prefix}{current_price:.2f}")
            except Exception as e:
                st.caption("Waiting for live price data...")

        with colA:
            st.subheader(f"📊 Market Reaction (1m)")
            try:
                if not ai_chart_data.empty:
                    if isinstance(ai_chart_data.columns, pd.MultiIndex):
                        ai_chart_data.columns = ai_chart_data.columns.droplevel(1)
                    fig2 = go.Figure(data=[go.Candlestick(
                        x=ai_chart_data.index, open=ai_chart_data['Open'], 
                        high=ai_chart_data['High'], low=ai_chart_data['Low'], 
                        close=ai_chart_data['Close'], name=target_ticker
                    )])
                    fig2.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=350, margin=dict(l=0, r=0, t=0, b=0))
                    st.plotly_chart(fig2, use_container_width=True)
            except Exception as e:
                st.error(f"Chart Error: {e}")

# ==========================================
# TAB 3: AUTONOMOUS AGENT SIMULATOR
# ==========================================
with tab3:
    if not st.session_state.news_df.empty:
        df = st.session_state.news_df
        st.markdown("### 🧠 Agentic Portfolio & Risk Manager")
        
        total_news = len(df)
        bullish_count = len(df[df['sentiment'] == 'Bullish'])
        bull_pct = (bullish_count / total_news) * 100 if total_news > 0 else 50
        
        if bull_pct >= 60:
            risk_level, cash_allocation, risk_color = "AGGRESSIVE (Risk-On)", "20% Cash / 80% Equities", "🟢"
        elif bull_pct <= 40:
            risk_level, cash_allocation, risk_color = "DEFENSIVE (Risk-Off)", "80% Cash / 20% Equities", "🔴"
        else:
            risk_level, cash_allocation, risk_color = "BALANCED (Neutral)", "50% Cash / 50% Equities", "🟡"
            
        r_col1, r_col2, r_col3 = st.columns(3)
        r_col1.metric("Macro Market Sentiment", f"{bull_pct:.1f}% Bullish")
        r_col2.metric("Agent Risk Posture", f"{risk_color} {risk_level}")
        r_col3.metric("Target Portfolio Allocation", cash_allocation)
            
        st.markdown("---")
        st.markdown("#### ⚡ Automated Execution Engine")
        
        trade_log = []
        for _, row in df.iterrows():
            ticker = str(row.get('ticker', 'SPY')).upper()
            sentiment = str(row.get('sentiment', 'Neutral')).capitalize()
            try: conf = int(row.get('confidence', 50))
            except: conf = 50
            
            if ticker not in ['SPY', 'NONE', '']:
                if sentiment == 'Bullish' and conf >= 75:
                    trade_log.append({"Time": time.strftime("%H:%M:%S"), "Action": "🟢 BUY", "Ticker": ticker, "Size": "Aggressive" if conf>=90 else "Standard", "Confidence": f"{conf}%", "Trigger": row['headline']})
                elif sentiment == 'Bearish' and conf >= 75:
                    trade_log.append({"Time": time.strftime("%H:%M:%S"), "Action": "🔴 SELL", "Ticker": ticker, "Size": "Aggressive" if conf>=90 else "Standard", "Confidence": f"{conf}%", "Trigger": row['headline']})

        if trade_log:
            st.dataframe(pd.DataFrame(trade_log), use_container_width=True, hide_index=True)
        else:
            st.info("Agent Status: Holding Cash. No high-confidence actionable setups found.")
# ==========================================
# TAB 4: INSTITUTIONAL SMC ALGORITHM
# ==========================================
with tab4:
    st.markdown("### 📐 Smart Money Concepts (SMC) Engine")
    st.caption("Advanced Technical Analysis: Multi-Timeframe Structure, FVGs, and Liquidity.")
    
    # User Control Panel
    st.markdown("#### ⚙️ Strategy Configuration")
    
    # Let the user pick a specific coin/stock to run the SMC math on
    smc_selected = st.selectbox("Select Asset for SMC Analysis:", POPULAR_STOCKS, key="smc_combo")
    smc_ticker = smc_selected.split(" - ")[0].strip()
    
    colA, colB = st.columns(2)
    with colA:
        strategy = st.selectbox("Trading Model:", [
            "Mean Reversion (FVG Fill)", 
            "Break & Retest (Trend Follow)", 
            "Liquidity Sweep"
        ])
    with colB:
        risk_profile = st.selectbox("Risk/Reward Ratio:", [
            "1:2 (Conservative)", 
            "1:3 (Standard)", 
            "1:5 (Aggressive Prop Firm)"
        ])
        
    st.markdown("---")
    
    # THE EXECUTION BUTTON
    if st.button("🧠 Run SMC Quant Math", use_container_width=True):
        with st.spinner(f"Dev 1's Math Engine is calculating exact levels for {smc_ticker}..."):
            try:
                # 1. Fetch 5-Minute Data (Best for SMC / FVG detection)
                smc_data = yf.download(smc_ticker, period="5d", interval="5m")
                
                if not smc_data.empty:
                    # Clean up Yahoo Finance multi-index weirdness
                    if isinstance(smc_data.columns, pd.MultiIndex):
                        smc_data.columns = smc_data.columns.droplevel(1)
                        
                    # 2. CALL DEV 1's MATH ENGINE!
                    setup = generate_smc_signal(smc_data, strategy, risk_profile)
                    
                    # 3. RENDER THE RESULTS TO THE UI
                    st.markdown("#### ⚡ Live Trade Setup")
                    
                    # Smart Currency formatter (Rupees vs Dollars)
                    currency = "₹" if ".NS" in smc_ticker else "$"
                    
                    res_col1, res_col2, res_col3, res_col4 = st.columns(4)
                    res_col1.metric("Action Signal", setup["signal"])
                    res_col2.metric("Entry Price", f"{currency}{setup['entry']:.2f}")
                    
                    # Only show SL/TP if a valid setup was actually found
                    if setup["sl"] > 0:
                        res_col3.metric("Stop Loss (SL)", f"{currency}{setup['sl']:.2f}")
                        res_col4.metric("Take Profit (TP)", f"{currency}{setup['tp']:.2f}")
                    else:
                        res_col3.metric("Stop Loss (SL)", "--")
                        res_col4.metric("Take Profit (TP)", "--")
                        
                    st.info(f"**🤖 Quant Logic:** {setup['logic']}")
                    
                else:
                    st.warning("⚠️ No recent market data found to run SMC math.")
            except Exception as e:
                st.error(f"SMC Engine Error: {e}")

# --- LIVE AUTO REFRESH CLOCK ---
st.markdown("---")
auto_col1, auto_col2 = st.columns([1, 4])
with auto_col1:
    auto_refresh = st.toggle("🔴 Live Auto-Refresh (1m)")
with auto_col2:
    if auto_refresh:
        timer_placeholder = st.empty()
        for i in range(60, 0, -1):
            timer_placeholder.caption(f"⏳ Next live market tick in **{i}** seconds...")
            time.sleep(1)
        st.rerun()
