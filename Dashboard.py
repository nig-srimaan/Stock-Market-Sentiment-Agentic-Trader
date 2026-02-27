import streamlit as st
import pandas as pd
import time

# --- 1. PORTFOLIO MEMORY (SESSION STATE) ---
# This ensures the app remembers your money and stocks when it refreshes
if 'cash' not in st.session_state:
    st.session_state.cash = 10000.00
if 'holdings' not in st.session_state:
    st.session_state.holdings = {"AAPL": 0, "MSFT": 0, "TSLA": 0}
if 'logs' not in st.session_state:
    st.session_state.logs = ["🟢 [SYSTEM] Portfolio memory initialized."]

# --- 2. TRADING LOGIC (THE ENGINE) ---
def execute_trade(action, ticker, shares, price):
    cost = shares * price
    if action == "BUY" and st.session_state.cash >= cost:
        st.session_state.cash -= cost
        st.session_state.holdings[ticker] += shares
        st.session_state.logs.insert(0, f"🔵 [TRADE] BOUGHT {shares} {ticker} @ ${price} (-${cost})")
    elif action == "SELL" and st.session_state.holdings[ticker] >= shares:
        st.session_state.cash += cost
        st.session_state.holdings[ticker] -= shares
        st.session_state.logs.insert(0, f"🟠 [TRADE] SOLD {shares} {ticker} @ ${price} (+${cost})")
    else:
        st.session_state.logs.insert(0, f"🔴 [ERROR] Trade failed: Insufficient funds or shares for {ticker}.")


# --- 3. THE USER INTERFACE ---
st.set_page_config(page_title="AI Agentic Trader", layout="wide")
st.title("📈 Stock Market Sentiment Agentic Trader")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("💼 Portfolio Status")
    
    # Now the cash updates dynamically!
    st.metric(label="Current Cash Balance", value=f"${st.session_state.cash:,.2f}")
    
    st.subheader("Current Holdings")
    # Convert our memory dictionary into a nice table
    df_holdings = pd.DataFrame(list(st.session_state.holdings.items()), columns=['Ticker', 'Shares'])
    st.dataframe(df_holdings, hide_index=True, use_container_width=True)

with col2:
    st.header("📰 Live AI Sentiment Analysis")
    st.info("Waiting for Dev 1's Live Data Engine...")
    
    # --- DEV 2 TESTING AREA ---
    st.subheader("🛠️ Dev 2 Testing Tools")
    st.caption("Use this to test the portfolio math before Dev 1 connects the AI.")
    
    test_col1, test_col2 = st.columns(2)
    with test_col1:
        if st.button("Simulate AI: BULLISH AAPL (Buy 5)"):
            execute_trade("BUY", "AAPL", 5, 150.00)
            st.rerun() # Forces the screen to update
    with test_col2:
        if st.button("Simulate AI: BEARISH AAPL (Sell 5)"):
            execute_trade("SELL", "AAPL", 5, 155.00)
            st.rerun()
            
    # --- LOGS ---
    st.subheader("Recent Agent Actions")
    for log in st.session_state.logs[:5]: # Show the 5 most recent logs
        st.write(log)