import streamlit as st
import pandas as pd

# 1. Set up the page layout
st.set_page_config(page_title="AI Agentic Trader", layout="wide")

st.title("📈 Stock Market Sentiment Agentic Trader")
st.markdown("Welcome to the Dashboard. The AI Agent analyzes news and trades automatically based on market sentiment.")

# 2. Create two columns: one for Portfolio, one for Live News
col1, col2 = st.columns([1, 2])

# --- COLUMN 1: THE PORTFOLIO ---
with col1:
    st.header("💼 Portfolio Status")
    
    # Mock starting balance
    st.metric(label="Current Cash Balance", value="$10,000.00", delta="0.00")
    st.metric(label="Current Risk Level", value="Medium")
    
    st.subheader("Current Holdings")
    # A dummy table to show what stocks the bot "owns" right now
    holdings = pd.DataFrame({
        "Ticker": ["AAPL", "MSFT"],
        "Shares": [10, 5],
        "Value": ["$1,750", "$2,100"]
    })
    st.dataframe(holdings, hide_index=True)

# --- COLUMN 2: THE AI BRAIN ---
with col2:
    st.header("📰 Live AI Sentiment Analysis")
    
    # This is a placeholder until Dev 1 connects their scraper
    st.info("⏳ Waiting for Data Engine (Dev 1) to send live news...")
    
    st.subheader("Recent Agent Actions")
    # A mock log of what the bot is doing
    st.write("🟢 **[SYSTEM]** AI Agent initialized and ready.")
    st.write("🟡 **[STANDBY]** Waiting for sentiment triggers to execute trades.")