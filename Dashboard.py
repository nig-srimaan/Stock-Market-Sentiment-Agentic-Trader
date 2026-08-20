import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import json
import time  
import streamlit.components.v1 as components

# ==========================================
# --- OUR CUSTOM ENGINES ---
# ==========================================
try:
    from llm_engine import analyze_sentiment_batch
    from scraper import fetch_financial_news
except ImportError:
    pass # Will gracefully skip if your local engine files aren't found
# Note: smc_engine.py's generate_smc_signal is NOT used here — this dashboard's
# SMC tab has its own detect_fvg / detect_liquidity_sweep / detect_break_and_retest
# functions defined below. smc_engine.py is kept in the repo as a standalone module
# but is not wired into this dashboard.

st.set_page_config(page_title="Agentic Stock Scanner", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 🚀 ULTRA-DYNAMIC CYBER UI (ANIMATED CSS)
# ==========================================
st.markdown("""
<style>
    /* Animated Background */
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .stApp {
        background: linear-gradient(-45deg, #0a0f18, #111827, #0d1423, #05080f);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
        color: #E2E8F0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Glowing Title */
    @keyframes pulseGlow {
        0% { text-shadow: 0 0 10px rgba(0,255,170,0.5); }
        50% { text-shadow: 0 0 25px rgba(0,255,170,0.9), 0 0 35px rgba(0,136,255,0.6); }
        100% { text-shadow: 0 0 10px rgba(0,255,170,0.5); }
    }
    h1 {
        background: linear-gradient(90deg, #00FFAA, #0088FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Trebuchet MS', sans-serif;
        font-weight: 900;
        animation: pulseGlow 3s infinite alternate;
    }
    
    /* Hover Metric Cards */
    [data-testid="stMetric"] {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-top: 2px solid #0088FF;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        position: relative;
        overflow: hidden;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-5px) scale(1.02);
        border-top: 2px solid #00FFAA;
        box-shadow: 0 15px 35px rgba(0, 255, 170, 0.2);
    }
    
    /* Custom Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 8px 8px 0px 0px;
        padding: 12px 24px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-bottom: none;
        color: #94A3B8;
        font-weight: 600;
        transition: 0.3s;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(180deg, rgba(0, 255, 170, 0.15) 0%, rgba(15, 23, 42, 0) 100%);
        color: #00FFAA !important;
        border-top: 2px solid #00FFAA !important;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #0088FF, #0055FF);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 700;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 136, 255, 0.3);
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #00FFAA, #0088FF);
        box-shadow: 0 0 20px rgba(0, 255, 170, 0.5);
        transform: scale(1.02);
        color: black;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 📐 SMC MATH & LOGIC
# ==========================================
def detect_fvg(df):
    fvg_bullish, fvg_bearish = [], []
    for i in range(2, len(df)):
        time_diff = (df.index[i] - df.index[i-2]).total_seconds()
        
        # Filter out overnight gaps (> 3 hours)
        if time_diff <= 10800: 
            if df['Low'].iloc[i] > df['High'].iloc[i-2]:  
                fvg_bullish.append({
                    'x0': df.index[i-2], 
                    'x1': df.index[min(i+15, len(df)-1)], 
                    'y0': df['High'].iloc[i-2], 
                    'y1': df['Low'].iloc[i]
                })
            elif df['High'].iloc[i] < df['Low'].iloc[i-2]: 
                fvg_bearish.append({
                    'x0': df.index[i-2], 
                    'x1': df.index[min(i+15, len(df)-1)], 
                    'y0': df['Low'].iloc[i-2], 
                    'y1': df['High'].iloc[i]
                })
    return fvg_bullish, fvg_bearish

def detect_liquidity_sweep(df, window=14, cooldown=None):
    """cooldown: minimum number of candles between two signals of the same
    type (Bullish/Bearish Sweep), so one structural event doesn't re-fire
    on every candle while price lingers near the swept level. Defaults to
    `window` candles."""
    if cooldown is None:
        cooldown = window
    sweeps = []
    rolling_high = df['High'].rolling(window=window).max().shift(1)
    rolling_low = df['Low'].rolling(window=window).min().shift(1)
    last_fire = {'Bearish Sweep': -cooldown, 'Bullish Sweep': -cooldown}
    
    for i in range(window, len(df)):
        if df['High'].iloc[i] > rolling_high.iloc[i] and df['Close'].iloc[i] < rolling_high.iloc[i]:
            if i - last_fire['Bearish Sweep'] >= cooldown:
                sweeps.append({'time': df.index[i], 'type': 'Bearish Sweep', 'price': df['High'].iloc[i]})
                last_fire['Bearish Sweep'] = i
        elif df['Low'].iloc[i] < rolling_low.iloc[i] and df['Close'].iloc[i] > rolling_low.iloc[i]:
            if i - last_fire['Bullish Sweep'] >= cooldown:
                sweeps.append({'time': df.index[i], 'type': 'Bullish Sweep', 'price': df['Low'].iloc[i]})
                last_fire['Bullish Sweep'] = i
    return sweeps

def detect_break_and_retest(df, window=14, margin=0.002, cooldown=None):
    """cooldown: see detect_liquidity_sweep — same fix, same reasoning."""
    if cooldown is None:
        cooldown = window
    signals = []
    last_fire = {'Bullish B&R': -cooldown, 'Bearish B&R': -cooldown}
    for i in range(window*2, len(df)):
        past_res = df['High'].iloc[i-window*2 : i-window].max()
        past_sup = df['Low'].iloc[i-window*2 : i-window].min()
        
        recent_breakout = df['Close'].iloc[i-window : i].max() > past_res
        retest_touch = (past_res * (1 - margin)) <= df['Low'].iloc[i] <= (past_res * (1 + margin))
        if recent_breakout and retest_touch and df['Close'].iloc[i] > df['Open'].iloc[i]:
            if i - last_fire['Bullish B&R'] >= cooldown:
                signals.append({'time': df.index[i], 'type': 'Bullish B&R', 'price': past_res})
                last_fire['Bullish B&R'] = i
            
        recent_breakdown = df['Close'].iloc[i-window : i].min() < past_sup
        retest_touch_bear = (past_sup * (1 - margin)) <= df['High'].iloc[i] <= (past_sup * (1 + margin))
        if recent_breakdown and retest_touch_bear and df['Close'].iloc[i] < df['Open'].iloc[i]:
            if i - last_fire['Bearish B&R'] >= cooldown:
                signals.append({'time': df.index[i], 'type': 'Bearish B&R', 'price': past_sup})
                last_fire['Bearish B&R'] = i
    return signals

def render_dynamic_chart(df, ticker_name, strategy_choice):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        increasing_line_color='#00FFAA', decreasing_line_color='#FF3366'
    )])

    # Add shapes/markers conditionally based on user choice
    if "FVG" in strategy_choice:
        bullish_fvgs, bearish_fvgs = detect_fvg(df)
        for fvg in bullish_fvgs:
            fig.add_shape(type="rect", x0=fvg['x0'], y0=fvg['y0'], x1=fvg['x1'], y1=fvg['y1'],
                          fillcolor="rgba(0, 255, 170, 0.2)", line=dict(width=0), layer="below")
        for fvg in bearish_fvgs:
            fig.add_shape(type="rect", x0=fvg['x0'], y0=fvg['y0'], x1=fvg['x1'], y1=fvg['y1'],
                          fillcolor="rgba(255, 51, 102, 0.2)", line=dict(width=0), layer="below")
                          
    elif "Sweep" in strategy_choice:
        sweeps = detect_liquidity_sweep(df)
        if sweeps:
            fig.add_trace(go.Scatter(
                x=[s['time'] for s in sweeps], y=[s['price'] for s in sweeps],
                mode='markers', marker=dict(symbol='x', size=10, color='orange'),
                hovertext=[s['type'] for s in sweeps], hoverinfo='text+x+y', name="Sweep"
            ))
            
    elif "Break" in strategy_choice:
        brs = detect_break_and_retest(df)
        if brs:
            fig.add_trace(go.Scatter(
                x=[s['time'] for s in brs], y=[s['price'] for s in brs],
                mode='markers', marker=dict(symbol='circle', size=10, color='cyan'),
                hovertext=[s['type'] for s in brs], hoverinfo='text+x+y', name="B&R"
            ))

    # Hide weekend gaps. NOTE: we deliberately do NOT add an intraday
    # "hide overnight hours" rangebreak here. Plotly's hour-pattern
    # rangebreaks need numeric hours + pattern="hour" (e.g.
    # bounds=[16, 9.5], pattern="hour") — the previous string-time format
    # ("16:00"/"09:30") was silently a no-op, which is why every trading
    # day rendered as a separate squished island with big gaps between
    # them. Switching to the correct numeric format works, BUT Plotly.js
    # has a known bug where hour-pattern rangebreaks can break candlestick
    # rendering (missing open/close boxes, broken hover). Given that's a
    # live-demo risk, we're keeping only the weekend skip — you'll see a
    # small flat gap between trading days instead, which is a safe
    # trade-off. If you want the intraday gaps removed too, the numeric
    # form is: dict(bounds=[16, 9.5], pattern="hour") for US or
    # dict(bounds=[15.5, 9.25], pattern="hour") for NSE — test it locally
    # first since it's a known-flaky combination with candlesticks.
    is_crypto = "-" in ticker_name and "USD" in ticker_name  # e.g. BTC-USD, ETH-USD
    if not is_crypto:
        fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])

    fig.update_layout(
        title=f"{ticker_name} - {strategy_choice} Analysis",
        xaxis_rangeslider_visible=False,
        template='plotly_dark',
        height=550,
        margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# ==========================================
# INITIALIZE MEMORY (SESSION STATE)
# ==========================================
if "news_df" not in st.session_state:
    st.session_state.news_df = pd.DataFrame()

if "has_scanned" not in st.session_state:
    st.session_state.has_scanned = False

if "smc_has_run" not in st.session_state:
    st.session_state.smc_has_run = False

if "news_is_fallback" not in st.session_state:
    st.session_state.news_is_fallback = False

POPULAR_STOCKS = [
    "NVDA - Nvidia Corp", "AAPL - Apple Inc", "MSFT - Microsoft", "TSLA - Tesla", 
    "AMZN - Amazon", "GOOGL - Alphabet (Google)", "META - Meta (Facebook)", "PLTR - Palantir",
    "SPY - S&P 500 Market Index", "QQQ - Nasdaq 100 Index", 
    "BTC-USD - Bitcoin", "ETH-USD - Ethereum", "SOL-USD - Solana",
    "RELIANCE.NS - Reliance Industries", "TCS.NS - Tata Consultancy Services", 
    "HDFCBANK.NS - HDFC Bank", "TATAMOTORS.NS - Tata Motors", "INFY.NS - Infosys"
]

# ==========================================
# SIDEBAR: AUTO-REFRESH CONFIG
# ==========================================
with st.sidebar:
    st.markdown("### ⚙️ Terminal Settings")
    auto_refresh = st.toggle("Enable Auto-Refresh", value=False)
    refresh_rate = st.slider("Refresh Interval (Seconds)", min_value=10, max_value=120, value=30)
    st.caption("Auto-refresh will automatically pull new YFinance data and recalculate SMC setups on a loop.")

st.title("Stockx📈")

# ==========================================
# ACTION 1: ONE-TIME BOOT SCANNER
# ==========================================
if not st.session_state.has_scanned:
    with st.spinner("🤖 System Booting: AI is analyzing live headlines..."):
        try:
            headlines, is_fallback = fetch_financial_news(count=15)
            st.session_state.news_is_fallback = is_fallback
            res = analyze_sentiment_batch(headlines)
            data = json.loads(res)
            if len(data) > 0:
                st.session_state.news_df = pd.DataFrame(data)
            else:
                st.error("Local AI returned empty data.")
        except Exception as e:
            st.warning(f"AI Scanning currently offline or misconfigured: {e}")
            
        st.session_state.has_scanned = True
        st.rerun()

# ==========================================
# UI TABS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 LIVE TERMINAL", 
    "📰 AI INTEL", 
    "🤖 AGENT SIMULATOR",
    "📐 SMC QUANT ENGINE"
])

# ==========================================
# TAB 1: LIVE TERMINAL (TRADINGVIEW WIDGET)
# ==========================================
with tab1:
    st.markdown("### 📈 Live Market Explorer (Tick-by-Tick)")
    selected_option = st.selectbox("Search Asset:", POPULAR_STOCKS)
    manual_ticker = selected_option.split(" - ")[0].strip()
    
    # Not every US ticker actually trades on NASDAQ — mapping the wrong
    # exchange makes the TradingView widget fail to load that symbol.
    EXCHANGE_MAP = {
        "SPY": "AMEX", "QQQ": "NASDAQ", "PLTR": "NYSE",
        "NVDA": "NASDAQ", "AAPL": "NASDAQ", "MSFT": "NASDAQ", "TSLA": "NASDAQ",
        "AMZN": "NASDAQ", "GOOGL": "NASDAQ", "META": "NASDAQ",
    }

    tv_ticker = manual_ticker
    if ".NS" in manual_ticker:
        tv_ticker = "NSE:" + manual_ticker.replace(".NS", "")
    elif "-" in manual_ticker:
        tv_ticker = "CRYPTO:" + manual_ticker.replace("-", "")
    else:
        exchange = EXCHANGE_MAP.get(manual_ticker, "NASDAQ")
        tv_ticker = f"{exchange}:{manual_ticker}"
    
    if manual_ticker:
        html_code = f"""
        <div class="tradingview-widget-container" style="height:600px;width:100%">
          <div id="tradingview_widget" style="height:100%;width:100%"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({{
          "autosize": true, "symbol": "{tv_ticker}", "interval": "1",
          "timezone": "exchange", "theme": "dark", "style": "1",
          "locale": "en", "enable_publishing": false, "backgroundColor": "rgba(13, 17, 23, 1)",
          "hide_top_toolbar": false, "save_image": false, "container_id": "tradingview_widget"
        }});
          </script>
        </div>
        """
        components.html(html_code, height=600)

# ==========================================
# TAB 2: AI NEWS FEED
# (wrapped in a fragment so its selectbox doesn't force a full-page
#  rerun that would reload the TradingView widget in Tab 1)
# ==========================================
@st.fragment
def render_ai_intel_tab():
    if not st.session_state.news_df.empty:
        df = st.session_state.news_df

        if st.session_state.get("news_is_fallback", False):
            st.warning("⚠️ FALLBACK DATA — live news scrape failed, showing offline sample headlines instead.")
        else:
            st.success("🟢 LIVE — headlines pulled from Google News just now.")

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
            st.subheader(f"🤖 Verdict & Targets")
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
                    # Fix pandas multi-index if yfinance returns it
                    if isinstance(ai_chart_data.columns, pd.MultiIndex):
                        ai_chart_data.columns = ai_chart_data.columns.droplevel(1)
                    
                    fig2 = go.Figure(data=[go.Candlestick(
                        x=ai_chart_data.index, open=ai_chart_data['Open'], 
                        high=ai_chart_data['High'], low=ai_chart_data['Low'], 
                        close=ai_chart_data['Close'], name=target_ticker
                    )])
                    fig2.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=350, margin=dict(l=0, r=0, t=0, b=0), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig2, use_container_width=True)
            except Exception as e:
                st.error(f"Chart Error: {e}")
    else:
        st.info("No AI data populated. The scanner may have returned an empty batch.")

with tab2:
    render_ai_intel_tab()

# ==========================================
# TAB 3: AUTONOMOUS AGENT SIMULATOR
# ==========================================
with tab3:
    if not st.session_state.news_df.empty:
        df = st.session_state.news_df
        st.markdown("### 🧠 Agentic Portfolio & Risk Manager")
        st.caption("Demonstrating real-time sentiment monitoring, dynamic risk adjustment, and automated trade logic.")
        
        st.markdown("#### ⚖️ Dynamic Risk Allocation")
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
                    size = "Aggressive Buy" if conf >= 90 else "Standard Buy"
                    trade_log.append({"Time": time.strftime("%H:%M:%S"), "Action": "🟢 BUY", "Ticker": ticker, "Size": size, "Confidence": f"{conf}%", "Trigger": row['headline']})
                elif sentiment == 'Bearish' and conf >= 75:
                    size = "Aggressive Short" if conf >= 90 else "Standard Sell"
                    trade_log.append({"Time": time.strftime("%H:%M:%S"), "Action": "🔴 SELL", "Ticker": ticker, "Size": size, "Confidence": f"{conf}%", "Trigger": row['headline']})

        if trade_log:
            st.dataframe(pd.DataFrame(trade_log), use_container_width=True, hide_index=True)
        else:
            st.info("Agent Status: Holding Cash. No high-confidence actionable setups found.")

# ==========================================
# TAB 4: SMC TECHNICAL ANALYSIS
# (wrapped in a fragment, with run_every doing the auto-refresh on its
#  own timer — this replaces the old sidebar toggle + st.rerun() combo,
#  which reran the ENTIRE script, including reloading Tab 1's live
#  TradingView widget, every refresh_rate seconds)
# ==========================================
@st.fragment(run_every=refresh_rate if auto_refresh else None)
def render_smc_tab():
    st.markdown("### 📐 Smart Money Concepts (SMC) Quant Engine")
    
    colA, colB, colC = st.columns([2, 1, 1])
    with colA:
        smc_selected = st.selectbox("Select Asset for SMC Analysis:", POPULAR_STOCKS, key="smc_combo")
        smc_ticker = smc_selected.split(" - ")[0].strip()
    with colB:
        strategy = st.selectbox("Trading Model:", ["Mean Reversion (FVG Fill)", "Break & Retest", "Liquidity Sweep"])
    with colC:
        risk_profile = st.selectbox("R/R Ratio:", ["1:2", "1:3", "1:5"])
        
    st.markdown("---")
    
    if st.button("🧠 Run SMC Quant Math", use_container_width=True):
        st.session_state.smc_has_run = True

    # Keep showing (and, if auto-refresh is on, keep re-pulling) results
    # after the first click — not just on the exact run the button was pressed.
    if st.session_state.get("smc_has_run", False):
        with st.spinner(f"Crunching math for {smc_ticker}..."):
            try:
                smc_data = yf.download(smc_ticker, period="5d", interval="5m")
                if not smc_data.empty:
                    # Fix multi-index dataframe structure from yfinance
                    if isinstance(smc_data.columns, pd.MultiIndex):
                        smc_data.columns = smc_data.columns.droplevel(1)
                        
                    chart_col, feed_col = st.columns([3, 1])
                    
                    with chart_col:
                        # Calls the DYNAMIC charting function
                        fig = render_dynamic_chart(smc_data, smc_ticker, strategy)
                        st.plotly_chart(fig, use_container_width=True)
                        
                    with feed_col:
                        st.markdown("#### 📡 Live Signal Scanner")
                        st.caption("Proof of calculations (Last 8 events)")
                        
                        sweeps = detect_liquidity_sweep(smc_data)
                        brs = detect_break_and_retest(smc_data)
                        
                        all_signals = sweeps + brs
                        all_signals.sort(key=lambda x: x['time'], reverse=True)
                        
                        if all_signals:
                            for sig in all_signals[:8]:
                                color = "🟢" if "Bullish" in sig['type'] else "🔴"
                                st.info(f"**{color} {sig['type']}**\n\nPrice: {sig['price']:.2f}\n\n`{sig['time'].strftime('%m-%d %H:%M')}`")
                        else:
                            st.warning("No recent B&R or Sweeps detected.")
                else:
                    st.warning("⚠️ No recent market data found.")
            except Exception as e:
                st.error(f"SMC Charting Error: {e}")

with tab4:
    render_smc_tab()
