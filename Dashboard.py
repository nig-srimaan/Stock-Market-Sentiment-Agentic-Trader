import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import json
from llm_engine import analyze_sentiment_batch
from scraper import fetch_financial_news

st.set_page_config(page_title="Agentic Stock Scanner", layout="wide")

# --- Initialize Memory (Session State) ---
if "news_df" not in st.session_state:
    st.session_state.news_df = pd.DataFrame()

# --- SIDEBAR: Control Panel ---
with st.sidebar:
    st.markdown("## 🕹️ Scanner Controls")
    num_headlines = st.slider("Headlines to Scan", 5, 30, 10)
    run_btn = st.button("🚀 Scan Live Market News", use_container_width=True)

st.title("📰 Interactive News-to-Chart Agent")

# --- ACTION 1: FETCH AND ANALYZE NEWS ---
if run_btn:
    with st.spinner("🤖 Local AI is analyzing headlines..."):
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

# --- ACTION 2: THE INTERACTIVE FEED ---
if not st.session_state.news_df.empty:
    df = st.session_state.news_df
    
    st.markdown("### 🎯 Select a Headline to Analyze its Stock")
    selected_headline = st.selectbox("Choose a breaking news story:", df['headline'].tolist())
    
    # --- SAFE EXTRACTION LAYER ---
    # We find the row for the selected headline
    # --- SAFE EXTRACTION LAYER ---
    selected_data = df[df['headline'] == selected_headline].iloc[0]
    
    # 1. Safe Ticker
    raw_ticker = selected_data.get('ticker', 'SPY')
    if pd.isna(raw_ticker) or str(raw_ticker).lower() == 'none' or raw_ticker == "":
        target_ticker = 'SPY'
    else:
        target_ticker = str(raw_ticker).upper()
        
    # 2. Safe Sentiment
    raw_sentiment = selected_data.get('sentiment', 'Neutral')
    if pd.isna(raw_sentiment) or str(raw_sentiment).lower() == 'none' or raw_sentiment == "":
        target_sentiment = 'Neutral'
    else:
        target_sentiment = str(raw_sentiment).capitalize()
        
    # 3. Safe Confidence
    raw_conf = selected_data.get('confidence', 50)
    if pd.isna(raw_conf) or str(raw_conf).lower() == 'none' or raw_conf == "":
        target_confidence = 50
    else:
        try:
            target_confidence = int(raw_conf)
        except ValueError:
            target_confidence = 50
            
    # 4. Safe Reasoning
    raw_logic = selected_data.get('reasoning', 'Awaiting further market catalysts.')
    if pd.isna(raw_logic) or str(raw_logic).lower() == 'none' or raw_logic == "":
        target_reasoning = 'Awaiting further market catalysts.'
    else:
        target_reasoning = str(raw_logic)
    
    # --- UI LAYOUT ---
    colA, colB = st.columns([3, 1])
    
    with colB:
        st.subheader(f"🤖 Agent Verdict")
        st.markdown(f"**Ticker Extracted:** `{target_ticker}`")
        
        # Sentiment-based styling
        if target_sentiment == 'Bullish':
            st.success(f"**Bias:** {target_sentiment} ({target_confidence}%)")
        elif target_sentiment == 'Bearish':
            st.error(f"**Bias:** {target_sentiment} ({target_confidence}%)")
        else:
            st.info(f"**Bias:** {target_sentiment} ({target_confidence}%)")
            
        st.markdown(f"**Logic:** *{target_reasoning}*")

    with colA:
        st.subheader(f"📊 {target_ticker} Live Chart")
        try:
            # Download 1 month of daily data
            chart_data = yf.download(target_ticker, period="1d", interval="1m")
            
            if not chart_data.empty:
                # Handle MultiIndex columns if necessary (specific to certain yfinance versions)
                if isinstance(chart_data.columns, pd.MultiIndex):
                    chart_data.columns = chart_data.columns.droplevel(1)
                    
                fig = go.Figure(data=[go.Candlestick(
                    x=chart_data.index, 
                    open=chart_data['Open'], 
                    high=chart_data['High'], 
                    low=chart_data['Low'], 
                    close=chart_data['Close'], 
                    name=target_ticker
                )])
                
                fig.update_layout(
                    xaxis_rangeslider_visible=False, 
                    template="plotly_dark", 
                    height=450, 
                    margin=dict(l=0, r=0, t=0, b=0)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"⚠️ Market data for '{target_ticker}' not found. Showing SPY instead.")
        except Exception as e:
            st.error(f"Chart Error for {target_ticker}: {e}")
else:
    st.info("👈 Click 'Scan Live Market News' in the sidebar to begin.")