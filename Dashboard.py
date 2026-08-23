import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import json
import time  
import streamlit.components.v1 as components

# ==========================================
# --- OUR CUSTOM ENGINES ---
# ==========================================
try:
    from llm_engine import analyze_sentiment_batch, analyze_tip
    from scraper import fetch_financial_news
except ImportError:
    pass # Will gracefully skip if your local engine files aren't found
# Note: smc_engine.py's generate_smc_signal is NOT used here — this dashboard's
# SMC tab has its own detect_fvg / detect_liquidity_sweep / detect_break_and_retest
# functions defined below. smc_engine.py is kept in the repo as a standalone module
# but is not wired into this dashboard.

st.set_page_config(page_title="Agentic Stock Scanner", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 📟 DESIGN SYSTEM — "SENTINEL" TERMINAL
# A market-surveillance desk, not a generic AI dashboard: near-black
# graphite, terminal amber, hairline dividers, monospace data. Red and
# green are reserved ONLY for actual bearish/bullish or risk/safe
# signals — never used decoratively.
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

    :root {
        --bg: #0A0B0D;
        --panel: #121417;
        --panel-2: #191C20;
        --border: rgba(255,255,255,0.08);
        --amber: #FFB300;
        --amber-dim: #8A5F00;
        --text: #E8E6DF;
        --text-dim: #7B818A;
        --risk: #FF4136;
        --safe: #2ECC71;
    }

    * { scrollbar-width: thin; scrollbar-color: var(--amber-dim) var(--bg); }
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: var(--bg); }
    ::-webkit-scrollbar-thumb { background: var(--amber-dim); border-radius: 0px; }

    .stApp { background: var(--bg); color: var(--text); font-family: 'IBM Plex Sans', sans-serif; }
    .block-container { padding-top: 1.2rem; }
    h1, h2, h3 { font-family: 'IBM Plex Mono', monospace; letter-spacing: -0.01em; }

    /* ---- Masthead ---- */
    .sentinel-header {
        display: flex; align-items: baseline; justify-content: space-between;
        border-bottom: 1px solid var(--border); padding-bottom: 12px;
    }
    .sentinel-title {
        font-family: 'IBM Plex Mono', monospace; font-size: 1.6rem; font-weight: 700;
        color: var(--amber); letter-spacing: 0.02em; margin: 0;
    }
    .sentinel-title span { color: var(--text-dim); font-weight: 400; font-size: 0.95rem; margin-left: 10px; }
    .sentinel-status {
        font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem;
        color: var(--safe); display: flex; align-items: center; gap: 6px;
    }
    .sentinel-dot {
        width: 7px; height: 7px; border-radius: 50%; background: var(--safe);
        box-shadow: 0 0 6px var(--safe); animation: blinkDot 1.6s ease-in-out infinite;
    }
    @keyframes blinkDot { 0%,100% { opacity: 1; } 50% { opacity: 0.25; } }

    /* ---- Ticker tape (signature element) ---- */
    .ticker-wrap {
        width: 100%; overflow: hidden; background: var(--panel);
        border-bottom: 1px solid var(--border); padding: 7px 0; margin-bottom: 22px;
    }
    .ticker-track {
        display: inline-block; white-space: nowrap;
        font-family: 'IBM Plex Mono', monospace; font-size: 0.82rem;
        animation: tickerScroll 32s linear infinite;
    }
    .ticker-track span { margin-right: 42px; color: var(--text-dim); }
    .ticker-track span.up { color: var(--safe); }
    .ticker-track span.down { color: var(--risk); }
    @keyframes tickerScroll { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }

    /* ---- Metric cards ---- */
    [data-testid="stMetric"] {
        background: var(--panel); border: 1px solid var(--border);
        border-left: 2px solid var(--amber); border-radius: 2px; padding: 16px 18px;
        transition: background 0.2s ease;
    }
    [data-testid="stMetric"]:hover { background: var(--panel-2); }
    [data-testid="stMetricLabel"] {
        font-family: 'IBM Plex Mono', monospace; color: var(--text-dim) !important;
        font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 0.05em;
    }
    [data-testid="stMetricValue"] { font-family: 'IBM Plex Mono', monospace; }

    /* ---- Tabs ---- */
    .stTabs [data-baseweb="tab-list"] { gap: 2px; background: transparent; border-bottom: 1px solid var(--border); }
    .stTabs [data-baseweb="tab"] {
        background: transparent; border-radius: 0; padding: 10px 20px; border: none;
        color: var(--text-dim); font-family: 'IBM Plex Mono', monospace; font-weight: 500;
        font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.04em;
        transition: color 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover { color: var(--text); }
    .stTabs [aria-selected="true"] {
        background: transparent !important; color: var(--amber) !important;
        border-bottom: 2px solid var(--amber) !important;
    }

    /* ---- Buttons ---- */
    .stButton>button {
        background: transparent; color: var(--amber); border: 1px solid var(--amber-dim);
        border-radius: 2px; padding: 8px 22px; font-family: 'IBM Plex Mono', monospace;
        font-weight: 600; font-size: 0.85rem; letter-spacing: 0.03em; transition: all 0.15s ease;
    }
    .stButton>button:hover { background: var(--amber); color: #0A0B0D; border-color: var(--amber); }

    /* ---- Alerts / Dataframes / Sidebar / Selects ---- */
    [data-testid="stAlert"] {
        border-radius: 2px; border: 1px solid var(--border);
        background: var(--panel); font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem;
    }
    [data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 2px; }
    [data-testid="stSidebar"] { background: var(--panel); border-right: 1px solid var(--border); }
    [data-testid="stSidebar"] * { font-family: 'IBM Plex Mono', monospace; }
    [data-baseweb="select"] > div {
        background: var(--panel) !important; border-color: var(--border) !important; border-radius: 2px !important;
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

def detect_volume_spike(df, window=20, threshold=2.5):
    """Flags whether the most recent candle's volume is anomalously high
    relative to its trailing rolling average — a hallmark of pump-and-dump
    activity (a burst of hype-driven trading with no organic build-up)."""
    if len(df) < window + 1:
        return {"flagged": False, "ratio": 1.0, "avg_volume": 0, "latest_volume": 0}
    avg_volume = df['Volume'].iloc[-(window + 1):-1].mean()
    latest_volume = df['Volume'].iloc[-1]
    ratio = (latest_volume / avg_volume) if avg_volume > 0 else 1.0
    return {
        "flagged": ratio >= threshold,
        "ratio": round(float(ratio), 2),
        "avg_volume": int(avg_volume),
        "latest_volume": int(latest_volume)
    }


# DEMO REFERENCE LIST ONLY — a handful of well-known SEBI-registered brokers/
# advisors, used to illustrate the advisor-verification signal. This is NOT
# a live connection to SEBI's actual registered-intermediary database.
SEBI_REGISTERED_SAMPLE = {
    "zerodha", "groww", "motilal oswal", "icici direct", "hdfc securities",
    "kotak securities", "angel one", "5paisa", "upstox", "sharekhan"
}

def check_advisor_registration(source_name):
    if not source_name or not source_name.strip():
        return {"checked": False, "registered": None}
    name_norm = source_name.strip().lower()
    is_registered = any(name_norm == s or name_norm in s or s in name_norm for s in SEBI_REGISTERED_SAMPLE)
    return {"checked": True, "registered": is_registered}


def compute_risk_score(manipulation_score, volume_spike, advisor_check, spike_threshold=2.5):
    """Weighted combination: tip language 45%, price/volume anomaly 35%,
    advisor registration status 20%. Kept simple and explainable on purpose —
    a judge (or a user) should be able to see exactly why a score landed
    where it did."""
    tip_component = manipulation_score
    volume_component = min((volume_spike['ratio'] / spike_threshold) * 100, 100) if volume_spike['ratio'] > 1 else 0
    if advisor_check['checked'] and advisor_check['registered'] is True:
        advisor_component = 0
    elif advisor_check['checked'] and advisor_check['registered'] is False:
        advisor_component = 100
    else:
        advisor_component = 60  # unverifiable / not provided — treated as moderate risk, not zero

    score = (tip_component * 0.45) + (volume_component * 0.35) + (advisor_component * 0.20)
    return max(0, min(100, round(score)))


def render_tip_analysis_chart(df, ticker_name, sweeps, volume_spike):
    """Two-row chart for the Tip Checker: price candles on top, volume below
    with the anomalous bar picked out in risk-red — this is the 'proof',
    not just a score. Also overlays any liquidity-sweep markers found."""
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3],
        vertical_spacing=0.03
    )

    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        increasing_line_color='#2ECC71', decreasing_line_color='#FF4136', name="Price"
    ), row=1, col=1)

    if sweeps:
        fig.add_trace(go.Scatter(
            x=[s['time'] for s in sweeps], y=[s['price'] for s in sweeps],
            mode='markers', marker=dict(symbol='x', size=10, color='#FFB300'),
            hovertext=[s['type'] for s in sweeps], hoverinfo='text+x+y', name="Sweep"
        ), row=1, col=1)

    bar_colors = ['#FF4136' if i == len(df) - 1 and volume_spike['flagged'] else 'rgba(123,129,138,0.5)'
                  for i in range(len(df))]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=bar_colors, name="Volume"), row=2, col=1)

    if not is_crypto_ticker(ticker_name):
        fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])

    fig.update_layout(
        height=550, showlegend=False, margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="IBM Plex Mono, monospace", color="#7B818A", size=11),
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)"), xaxis2=dict(gridcolor="rgba(255,255,255,0.06)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)"), yaxis2=dict(gridcolor="rgba(255,255,255,0.06)"),
        xaxis_rangeslider_visible=False,
    )
    return fig


def is_crypto_ticker(ticker_name):
    return "-" in ticker_name and "USD" in ticker_name


def render_dynamic_chart(df, ticker_name, strategy_choice):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        increasing_line_color='#2ECC71', decreasing_line_color='#FF4136'
    )])

    # Add shapes/markers conditionally based on user choice
    if "FVG" in strategy_choice:
        bullish_fvgs, bearish_fvgs = detect_fvg(df)
        for fvg in bullish_fvgs:
            fig.add_shape(type="rect", x0=fvg['x0'], y0=fvg['y0'], x1=fvg['x1'], y1=fvg['y1'],
                          fillcolor="rgba(46, 204, 113, 0.18)", line=dict(width=0), layer="below")
        for fvg in bearish_fvgs:
            fig.add_shape(type="rect", x0=fvg['x0'], y0=fvg['y0'], x1=fvg['x1'], y1=fvg['y1'],
                          fillcolor="rgba(255, 65, 54, 0.18)", line=dict(width=0), layer="below")
                          
    elif "Sweep" in strategy_choice:
        sweeps = detect_liquidity_sweep(df)
        if sweeps:
            fig.add_trace(go.Scatter(
                x=[s['time'] for s in sweeps], y=[s['price'] for s in sweeps],
                mode='markers', marker=dict(symbol='x', size=10, color='#FFB300'),
                hovertext=[s['type'] for s in sweeps], hoverinfo='text+x+y', name="Sweep"
            ))
            
    elif "Break" in strategy_choice:
        brs = detect_break_and_retest(df)
        if brs:
            fig.add_trace(go.Scatter(
                x=[s['time'] for s in brs], y=[s['price'] for s in brs],
                mode='markers', marker=dict(symbol='circle', size=10, color='#FFB300'),
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
    if not is_crypto_ticker(ticker_name):
        fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])

    fig.update_layout(
        title=dict(text=f"{ticker_name} — {strategy_choice}", font=dict(family="IBM Plex Mono, monospace", size=15, color="#E8E6DF")),
        xaxis_rangeslider_visible=False,
        font=dict(family="IBM Plex Mono, monospace", color="#7B818A", size=11),
        height=550,
        margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.06)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.06)"),
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

if "tip_analysis_result" not in st.session_state:
    st.session_state.tip_analysis_result = None

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

status_live = not st.session_state.get("news_is_fallback", False)
status_label = "LIVE FEED" if status_live else "FALLBACK DATA"
status_color = "var(--safe)" if status_live else "var(--risk)"

st.markdown(f"""
<div class="sentinel-header">
    <p class="sentinel-title">SENTINEL<span>// Retail Market Surveillance Terminal</span></p>
    <div class="sentinel-status" style="color:{status_color};">
        <span class="sentinel-dot" style="background:{status_color}; box-shadow:0 0 6px {status_color};"></span>
        {status_label}
    </div>
</div>
<div class="ticker-wrap">
    <div class="ticker-track">
        <span class="up">NIFTY 50 ▲ 24,812.35</span>
        <span class="down">RELIANCE.NS ▼ 2,847.10</span>
        <span class="up">SENSEX ▲ 81,204.88</span>
        <span class="down">TATAMOTORS.NS ▼ 1,012.40</span>
        <span class="up">NVDA ▲ 227.94</span>
        <span>HDFCBANK.NS — 1,684.05</span>
        <span class="down">INFY.NS ▼ 1,498.20</span>
        <span class="up">TCS.NS ▲ 4,221.55</span>
        <span class="up">NIFTY 50 ▲ 24,812.35</span>
        <span class="down">RELIANCE.NS ▼ 2,847.10</span>
        <span class="up">SENSEX ▲ 81,204.88</span>
        <span class="down">TATAMOTORS.NS ▼ 1,012.40</span>
        <span class="up">NVDA ▲ 227.94</span>
        <span>HDFCBANK.NS — 1,684.05</span>
        <span class="down">INFY.NS ▼ 1,498.20</span>
        <span class="up">TCS.NS ▲ 4,221.55</span>
    </div>
</div>
""", unsafe_allow_html=True)

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
# ==========================================
# TIP CHECKER — the primary interface, not a tab among others.
# Everything else SENTINEL can do lives in a secondary, collapsed
# section further down — this is what a user sees first.
# ==========================================
hero_left, hero_right = st.columns([2, 3], gap="large")

with hero_left:
    st.markdown("""
    <p style="font-family:'IBM Plex Mono',monospace;color:var(--amber);font-size:0.78rem;
       letter-spacing:0.08em;text-transform:uppercase;margin-bottom:10px;">Retail Investor Protection</p>
    <h1 style="margin:0 0 14px 0;font-size:2.3rem;line-height:1.18;font-family:'IBM Plex Mono',monospace;
       font-weight:700;">Check a tip<br>before you act on it.</h1>
    <p style="color:var(--text-dim);font-size:1rem;line-height:1.6;max-width:440px;margin-bottom:30px;">
       Paste any stock tip and SENTINEL cross-checks it against tip language, live price/volume behavior,
       and advisor registration — before you risk real money on it.</p>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="display:flex; gap:14px; flex-wrap:wrap; margin-bottom:8px;">
        <div style="border:1px solid var(--border); border-left:2px solid var(--amber); background:var(--panel);
             border-radius:2px; padding:12px 16px; flex:1; min-width:120px;">
            <p style="font-family:'IBM Plex Mono',monospace; font-size:1.4rem; font-weight:700; color:var(--amber); margin:0;">62%</p>
            <p style="color:var(--text-dim); font-size:0.72rem; margin:2px 0 0 0; line-height:1.3;">of retail investors influenced by finfluencers — SEBI FY26</p>
        </div>
        <div style="border:1px solid var(--border); border-left:2px solid var(--amber); background:var(--panel);
             border-radius:2px; padding:12px 16px; flex:1; min-width:120px;">
            <p style="font-family:'IBM Plex Mono',monospace; font-size:1.4rem; font-weight:700; color:var(--amber); margin:0;">3</p>
            <p style="color:var(--text-dim); font-size:0.72rem; margin:2px 0 0 0; line-height:1.3;">independent signals combined into one explainable score</p>
        </div>
        <div style="border:1px solid var(--border); border-left:2px solid var(--amber); background:var(--panel);
             border-radius:2px; padding:12px 16px; flex:1; min-width:120px;">
            <p style="font-family:'IBM Plex Mono',monospace; font-size:1.4rem; font-weight:700; color:var(--amber); margin:0;">0</p>
            <p style="color:var(--text-dim); font-size:0.72rem; margin:2px 0 0 0; line-height:1.3;">black boxes — every signal is shown, not hidden</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

with hero_right:
    with st.container(border=True):
        st.markdown("""<p style="font-family:'IBM Plex Mono',monospace; font-weight:600; font-size:0.95rem;
                     color:var(--text); margin-bottom:16px; display:flex; align-items:center; gap:8px;">
                     🛡️ RUN THE CHECK</p>""", unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            tip_ticker = st.text_input("Stock Ticker", placeholder="e.g. RELIANCE.NS or NVDA", key="tip_ticker_input")
        with col_b:
            tip_source = st.text_input("Source / Advisor Name (optional)", placeholder="e.g. Telegram channel, advisor name", key="tip_source_input")

        tip_text = st.text_area(
            "Paste the Tip",
            height=120,
            placeholder='e.g. "RELIANCE going to ₹3500 by Friday! Guaranteed multibagger, buy NOW before it\'s too late 🚀🚀🚀"',
            key="tip_text_input"
        )

        analyze_clicked = st.button("🔍 Analyze This Tip", use_container_width=True, key="analyze_tip_btn")

st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)

if analyze_clicked:
    if not tip_ticker.strip() or not tip_text.strip():
        st.warning("⚠️ Please provide both a ticker and the tip text.")
    else:
        with st.spinner("Running tip through the detection pipeline..."):
            tip_result_raw = analyze_tip(tip_text)
            try:
                tip_result = json.loads(tip_result_raw)
            except json.JSONDecodeError:
                tip_result = {"manipulation_score": 0, "red_flags": [], "ticker_mentioned": "", "reasoning": "Analysis failed"}

            try:
                price_df = yf.download(tip_ticker.strip(), period="5d", interval="5m", progress=False)
                if isinstance(price_df.columns, pd.MultiIndex):
                    price_df.columns = price_df.columns.droplevel(1)
            except Exception:
                price_df = pd.DataFrame()

            if not price_df.empty:
                volume_spike = detect_volume_spike(price_df)
                sweeps = detect_liquidity_sweep(price_df)
            else:
                volume_spike = {"flagged": False, "ratio": 1.0, "avg_volume": 0, "latest_volume": 0}
                sweeps = []

            advisor_check = check_advisor_registration(tip_source)
            risk_score = compute_risk_score(tip_result.get("manipulation_score", 0), volume_spike, advisor_check)

            st.session_state.tip_analysis_result = {
                "risk_score": risk_score, "tip_result": tip_result, "volume_spike": volume_spike,
                "sweeps": sweeps, "advisor_check": advisor_check, "price_df": price_df, "ticker": tip_ticker.strip()
            }

if st.session_state.get("tip_analysis_result"):
    res = st.session_state.tip_analysis_result
    score = res["risk_score"]
    if score >= 66:
        verdict, color = "HIGH RISK", "var(--risk)"
    elif score >= 33:
        verdict, color = "MEDIUM RISK", "var(--amber)"
    else:
        verdict, color = "LOW RISK", "var(--safe)"

    st.markdown(f"""
    <div style="border: 1px solid var(--border); border-left: 3px solid {color}; background: var(--panel); border-radius: 2px; padding: 20px 24px; margin: 20px 0;">
        <div style="display:flex; align-items:baseline; gap:16px;">
            <span style="font-family:'IBM Plex Mono',monospace; font-size:2.6rem; font-weight:700; color:{color};">{score}</span>
            <span style="font-family:'IBM Plex Mono',monospace; font-size:1.1rem; color:{color}; text-transform:uppercase; letter-spacing:0.04em;">{verdict}</span>
        </div>
        <p style="color:var(--text-dim); font-size:0.85rem; margin-top:8px;">Manipulation Risk Score — combining tip language (45%), price/volume behavior (35%), and advisor verification (20%)</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**📝 Tip Language**")
        st.metric("Manipulation Score", f"{res['tip_result'].get('manipulation_score', 0)}/100")
        flags = res['tip_result'].get('red_flags', [])
        if flags:
            for f in flags:
                st.markdown(f"- _{f}_")
        else:
            st.caption("No manipulation-language markers detected")
        if res['tip_result'].get('reasoning'):
            st.caption(res['tip_result']['reasoning'])

    with c2:
        st.markdown("**📊 Price/Volume Anomaly**")
        vs = res['volume_spike']
        st.metric("Volume vs. Average", f"{vs['ratio']}x")
        if vs['flagged']:
            st.markdown(f"🔴 Latest volume (**{vs['latest_volume']:,}**) is **{vs['ratio']}x** the 20-candle average (**{vs['avg_volume']:,}**) — consistent with artificial hype")
        else:
            st.caption("No abnormal volume spike detected")
        if res['sweeps']:
            st.caption(f"{len(res['sweeps'])} liquidity sweep(s) detected in recent price action")

    with c3:
        st.markdown("**✅ Advisor Verification**")
        ac = res['advisor_check']
        if not ac['checked']:
            st.caption("No source provided — treated as unverifiable")
        elif ac['registered']:
            st.markdown("🟢 Matches a known registered source")
        else:
            st.markdown("🔴 Not found in registered-advisor reference list")
        st.caption("Demo reference list only — not a live SEBI database lookup")

    if not res['price_df'].empty:
        st.markdown("#### Price & Volume Evidence")
        fig = render_tip_analysis_chart(res['price_df'], res['ticker'], res['sweeps'], res['volume_spike'])
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Red volume bar = the anomalous spike flagged above. Amber ✕ marks = liquidity sweeps (price wicking beyond a recent high/low and snapping back) — a pattern consistent with engineered price action, not organic trading.")
    else:
        st.info("Could not pull price/volume data for this ticker — showing tip-language and advisor signals only.")

# ==========================================
# TAB 1: LIVE TERMINAL (TRADINGVIEW WIDGET)
# ==========================================

# ==========================================
# SECONDARY: the existing market-intelligence tools this is built on.
# Collapsed by default -- supporting evidence, not competing for
# attention with the primary Tip Checker above.
# ==========================================
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("⚙️ Underlying Market Intelligence Engine (existing system)", expanded=False):
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 LIVE TERMINAL",
        "📰 AI INTEL",
        "🤖 AGENT SIMULATOR",
        "📐 SMC QUANT ENGINE"
    ])

    with tab1:
        st.markdown("### 📈 Live Market Explorer")
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
              "autosize": true, "symbol": "{tv_ticker}", "interval": "5",
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
                        fig2.update_layout(xaxis_rangeslider_visible=False, height=350, margin=dict(l=0, r=0, t=0, b=0), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(family="IBM Plex Mono, monospace", color="#7B818A", size=11), xaxis=dict(gridcolor="rgba(255,255,255,0.06)"), yaxis=dict(gridcolor="rgba(255,255,255,0.06)"))
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
