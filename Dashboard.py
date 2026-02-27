import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import json
import time  
from llm_engine import analyze_sentiment_batch
from scraper import fetch_financial_news

st.set_page_config(page_title="Agentic Stock Scanner", layout="wide")

# --- Initialize Memory (Session State) ---
if "news_df" not in st.session_state:
    st.session_state.news_df = pd.DataFrame()

# --- THE SMART TICKER DICTIONARY ---
POPULAR_STOCKS = [
    "NVDA - Nvidia Corp", "AAPL - Apple Inc", "MSFT - Microsoft", "TSLA - Tesla", 
    "AMZN - Amazon", "GOOGL - Alphabet (Google)", "META - Meta (Facebook)", "PLTR - Palantir",
    "SPY - S&P 500 Market Index", "QQQ - Nasdaq 100 Index", 
    "BTC-USD - Bitcoin", "ETH-USD - Ethereum", "SOL-USD - Solana",
    "RELIANCE.NS - Reliance Industries", "TCS.NS - Tata Consultancy Services", 
    "HDFCBANK.NS - HDFC Bank", "TATAMOTORS.NS - Tata Motors", "INFY.NS - Infosys"
]

st.title("⚡ Agentic Trading Terminal")

# --- ACTION 1: AUTOMATIC BACKGROUND AI SCANNER ---
if st.session_state.news_df.empty:
    with st.spinner("🤖 System Booting: AI is analyzing global headlines... (This may take a minute)"):
        headlines = fetch_financial_news(count=50) 
        res = analyze_sentiment_batch(headlines)
        
        try:
            data = json.loads(res)
            if len(data) > 0:
                st.session_state.news_df = pd.DataFrame(data)
                st.rerun()
            else:
                st.error("Local AI returned empty data. Please check connection.")
        except Exception as e:
            st.error(f"Format error from Local AI: {e}")

# --- CREATE TABS FOR CLEAN UI ---
# ADDED THE 3RD TAB FOR THE AGENT SIMULATOR!
tab1, tab2, tab3 = st.tabs(["🔍 Market Explorer", "📰 AI Intelligence Feed", "🤖 Autonomous Trading Agent"])

# ==========================================
# TAB 1: MANUAL SEARCH BAR
# ==========================================
with tab1:
    st.markdown("### 📈 Live Market Explorer")
    selected_option = st.selectbox("Search for a Company, Ticker, or Crypto:", POPULAR_STOCKS)
    manual_ticker = selected_option.split(" - ")[0].strip()
    
    if manual_ticker:
        try:
            chart_data = yf.download(manual_ticker, period="1d", interval="1m")
            if not chart_data.empty:
                if isinstance(chart_data.columns, pd.MultiIndex):
                    chart_data.columns = chart_data.columns.droplevel(1)
                    
                fig = go.Figure(data=[go.Candlestick(
                    x=chart_data.index, 
                    open=chart_data['Open'], 
                    high=chart_data['High'], 
                    low=chart_data['Low'], 
                    close=chart_data['Close'], 
                    name=manual_ticker
                )])
                
                fig.update_layout(
                    xaxis_rangeslider_visible=False, 
                    template="plotly_dark", 
                    height=450, 
                    margin=dict(l=0, r=0, t=0, b=0),
                    title=f"Live 1m Chart: {selected_option}"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"⚠️ Market data for '{manual_ticker}' not found yet today.")
        except Exception as e:
            st.error(f"Chart Error: {e}")

# ==========================================
# TAB 2: AI NEWS FEED
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
        selected_headline = st.selectbox("Select a breaking news story from the AI feed to chart:", df['headline'].tolist())
        selected_data = df[df['headline'] == selected_headline].iloc[0]
        
        target_ticker = str(selected_data.get('ticker', 'SPY')).upper()
        if target_ticker in ['NONE', 'NAN', '']: target_ticker = 'SPY'
        target_sentiment = str(selected_data.get('sentiment', 'Neutral')).capitalize()
        target_reasoning = str(selected_data.get('reasoning', 'Awaiting catalysts.'))
        try: target_confidence = int(selected_data.get('confidence', 50))
        except: target_confidence = 50
        
        colA, colB = st.columns([3, 1])
        with colB:
            st.subheader(f"🤖 Verdict")
            st.markdown(f"**Ticker Extracted:** `{target_ticker}`")
            if target_sentiment == 'Bullish': st.success(f"**Bias:** {target_sentiment} ({target_confidence}%)")
            elif target_sentiment == 'Bearish': st.error(f"**Bias:** {target_sentiment} ({target_confidence}%)")
            else: st.info(f"**Bias:** {target_sentiment} ({target_confidence}%)")
            st.markdown(f"**Logic:** *{target_reasoning}*")

        with colA:
            st.subheader(f"📊 Market Reaction (1m)")
            try:
                ai_chart_data = yf.download(target_ticker, period="1d", interval="1m")
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
        st.caption("Demonstrating real-time sentiment monitoring, dynamic risk adjustment, and automated trade logic.")
        
        # --- 1. REAL-TIME SENTIMENT & RISK MONITOR ---
        st.markdown("#### ⚖️ Dynamic Risk Allocation")
        
        total_news = len(df)
        bullish_count = len(df[df['sentiment'] == 'Bullish'])
        bearish_count = len(df[df['sentiment'] == 'Bearish'])
        
        # Calculate Macro Market Sentiment
        bull_pct = (bullish_count / total_news) * 100 if total_news > 0 else 50
        
        # Dynamic Risk Adjustment Logic
        if bull_pct >= 60:
            risk_level = "AGGRESSIVE (Risk-On)"
            cash_allocation = "20% Cash / 80% Equities"
            risk_color = "🟢"
        elif bull_pct <= 40:
            risk_level = "DEFENSIVE (Risk-Off)"
            cash_allocation = "80% Cash / 20% Equities"
            risk_color = "🔴"
        else:
            risk_level = "BALANCED (Neutral)"
            cash_allocation = "50% Cash / 50% Equities"
            risk_color = "🟡"
            
        r_col1, r_col2, r_col3 = st.columns(3)
        with r_col1:
            st.metric("Macro Market Sentiment", f"{bull_pct:.1f}% Bullish")
        with r_col2:
            st.metric("Agent Risk Posture", f"{risk_color} {risk_level}")
        with r_col3:
            st.metric("Target Portfolio Allocation", cash_allocation)
            
        st.markdown("---")
        
        # --- 2. AUTOMATED SENTIMENT-DRIVEN TRADING LOG ---
        st.markdown("#### ⚡ Automated Execution Engine")
        
        trade_log = []
        for _, row in df.iterrows():
            ticker = str(row.get('ticker', 'SPY')).upper()
            sentiment = str(row.get('sentiment', 'Neutral')).capitalize()
            try: conf = int(row.get('confidence', 50))
            except: conf = 50
            
            # Agentic Logic: Only execute on specific companies with HIGH confidence
            if ticker != 'SPY' and ticker != 'NONE':
                if sentiment == 'Bullish' and conf >= 75:
                    size = "Aggressive Buy" if conf >= 90 else "Standard Buy"
                    trade_log.append({"Time": time.strftime("%H:%M:%S"), "Action": "🟢 BUY", "Ticker": ticker, "Size": size, "Confidence": f"{conf}%", "Trigger": row['headline']})
                elif sentiment == 'Bearish' and conf >= 75:
                    size = "Aggressive Short" if conf >= 90 else "Standard Sell"
                    trade_log.append({"Time": time.strftime("%H:%M:%S"), "Action": "🔴 SELL", "Ticker": ticker, "Size": size, "Confidence": f"{conf}%", "Trigger": row['headline']})

        if trade_log:
            st.dataframe(pd.DataFrame(trade_log), use_container_width=True, hide_index=True)
        else:
            st.info("Agent Status: Holding Cash. No high-confidence actionable setups found in the current news cycle.")

# ==========================================
# THE LIVE TICKING CLOCK HACK
# ==========================================
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