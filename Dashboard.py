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

# --- SIDEBAR: Control Panel ---
with st.sidebar:
    st.markdown("## 🕹️ AI Scanner Controls")
    num_headlines = st.slider("Headlines to Scan", 5, 100, 15)
    run_btn = st.button("🚀 Scan Live Market News", use_container_width=True)

st.title("⚡ Agentic Trading Terminal")

# --- ACTION 1: FETCH AND ANALYZE NEWS ---
if run_btn:
    with st.spinner(f"🤖 Local AI is analyzing {num_headlines} headlines... (Let it cook)"):
        headlines = fetch_financial_news(count=num_headlines)
        res = analyze_sentiment_batch(headlines)
        
        try:
            data = json.loads(res)
            if len(data) > 0:
                st.session_state.news_df = pd.DataFrame(data)
            else:
                st.error("Local AI returned empty data.")
        except Exception as e:
            st.error(f"Format error from Local AI: {e}")

# --- CREATE TABS FOR CLEAN UI ---
tab1, tab2 = st.tabs(["🔍 Manual Market Search", "📰 AI News Scanner Feed"])

# ==========================================
# TAB 1: MANUAL SEARCH BAR
# ==========================================
with tab1:
    st.markdown("### 📈 Live Market Explorer")
    
    # 1. The Search Bar
    search_query = st.text_input("Enter any Global Ticker (e.g., NVDA, TSLA, RELIANCE.NS, BTC-USD):", value="NVDA")
    manual_ticker = search_query.upper().strip()
    
    # 2. The Chart
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
                    title=f"Live 1m Chart: {manual_ticker}"
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
        
        # Display the raw data cleanly
        display_df = df[['ticker', 'sentiment', 'confidence', 'headline', 'reasoning']].copy()
        display_df.columns = ['Ticker', 'Trend', 'Confidence (%)', 'Headline', 'AI Logic']
        
        # Show as an interactive Streamlit dataframe
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("### 🎯 Deep Dive Analysis")
        selected_headline = st.selectbox("Choose a breaking news story to chart:", df['headline'].tolist())
        
        # --- SAFE EXTRACTION LAYER ---
        selected_data = df[df['headline'] == selected_headline].iloc[0]
        
        target_ticker = str(selected_data.get('ticker', 'SPY')).upper()
        if target_ticker == 'NONE' or target_ticker == 'NAN': target_ticker = 'SPY'
            
        target_sentiment = str(selected_data.get('sentiment', 'Neutral')).capitalize()
        target_reasoning = str(selected_data.get('reasoning', 'Awaiting catalysts.'))
        
        try:
            target_confidence = int(selected_data.get('confidence', 50))
        except:
            target_confidence = 50
        
        # --- UI LAYOUT FOR DEEP DIVE ---
        colA, colB = st.columns([3, 1])
        
        with colB:
            st.subheader(f"🤖 Verdict")
            st.markdown(f"**Ticker:** `{target_ticker}`")
            
            if target_sentiment == 'Bullish':
                st.success(f"**Bias:** {target_sentiment} ({target_confidence}%)")
            elif target_sentiment == 'Bearish':
                st.error(f"**Bias:** {target_sentiment} ({target_confidence}%)")
            else:
                st.info(f"**Bias:** {target_sentiment} ({target_confidence}%)")
                
            st.markdown(f"**Logic:** *{target_reasoning}*")

        with colA:
            st.subheader(f"📊 {target_ticker} Reaction (1m)")
            try:
                ai_chart_data = yf.download(target_ticker, period="1d", interval="1m")
                
                if not ai_chart_data.empty:
                    if isinstance(ai_chart_data.columns, pd.MultiIndex):
                        ai_chart_data.columns = ai_chart_data.columns.droplevel(1)
                        
                    fig2 = go.Figure(data=[go.Candlestick(
                        x=ai_chart_data.index, 
                        open=ai_chart_data['Open'], 
                        high=ai_chart_data['High'], 
                        low=ai_chart_data['Low'], 
                        close=ai_chart_data['Close'], 
                        name=target_ticker
                    )])
                    
                    fig2.update_layout(
                        xaxis_rangeslider_visible=False, 
                        template="plotly_dark", 
                        height=350, 
                        margin=dict(l=0, r=0, t=0, b=0)
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.warning(f"⚠️ Live market data for '{target_ticker}' not found.")
            except Exception as e:
                st.error(f"Chart Error: {e}")
    else:
        st.info("👈 Click 'Scan Live Market News' in the sidebar to populate the AI Feed.")

# --- THE LIVE AUTO-REFRESH HACK ---
st.markdown("---")
auto_col1, auto_col2 = st.columns([1, 4])

with auto_col1:
    auto_refresh = st.toggle("🔴 Live Auto-Refresh (1m)")
    
with auto_col2:
    if auto_refresh:
        st.caption("⏳ Auto-refreshing data in 60 seconds...")
        time.sleep(60)
        st.rerun()