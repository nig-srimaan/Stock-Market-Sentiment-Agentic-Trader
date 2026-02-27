import pandas as pd
import numpy as np

def identify_swings(df, window=5):
    """
    Finds Support and Resistance zones by calculating Swing Highs (Resistance) 
    and Swing Lows (Support) over a rolling window.
    """
    # A Swing High is the highest price within the window (e.g., 5 candles before & after)
    df['Swing_High'] = df['High'] == df['High'].rolling(window=(window*2)+1, center=True).max()
    # A Swing Low is the lowest price within the window
    df['Swing_Low'] = df['Low'] == df['Low'].rolling(window=(window*2)+1, center=True).min()
    return df

def detect_fvgs(df):
    """
    Mathematically detects Fair Value Gaps (Imbalances).
    """
    # Bullish FVG: Gap between Candle 1 High and Candle 3 Low
    df['Bullish_FVG'] = df['Low'] > df['High'].shift(2)
    
    # Bearish FVG: Gap between Candle 1 Low and Candle 3 High
    df['Bearish_FVG'] = df['High'] < df['Low'].shift(2)
    return df

def generate_smc_signal(df, strategy, rr_ratio):
    """
    The Core Decision Engine. 
    It reads the data, finds a setup, and calculates exact SL & TP targets.
    """
    df = identify_swings(df)
    df = detect_fvgs(df)
    
    # Get the current market price
    current_price = df['Close'].iloc[-1]
    
    # Look at the last 10 candles for recent setups
    recent_data = df.tail(10)
    
    setup = {
        "signal": "NEUTRAL", 
        "entry": current_price,
        "sl": 0.0,
        "tp": 0.0,
        "logic": "Waiting for high-probability setup."
    }
    
    # --- PARSE THE RR RATIO ---
    # If UI sends "1:3 (Standard)", we extract the '3' for our math.
    try:
        reward_multiplier = int(rr_ratio.split(":")[1].split()[0])
    except:
        reward_multiplier = 2 # Default to 1:2 if parsing fails
        
    # --- STRATEGY 1: FVG MEAN REVERSION ---
    if "Mean Reversion" in strategy or "FVG" in strategy:
        if recent_data['Bullish_FVG'].any():
            # Found a Bullish FVG! We want to BUY when it dips into the gap.
            setup["signal"] = "🟢 BUY"
            setup["logic"] = "Bullish FVG detected. Buying the re-test."
            
            # SL goes just below the recent Swing Low for safety
            recent_lows = df[df['Swing_Low'] == True]['Low']
            setup["sl"] = recent_lows.iloc[-1] if not recent_lows.empty else current_price * 0.99
            
            # Calculate Risk to find the Take Profit
            risk = setup["entry"] - setup["sl"]
            setup["tp"] = setup["entry"] + (risk * reward_multiplier)
            
        elif recent_data['Bearish_FVG'].any():
            # Found a Bearish FVG! We want to SELL (Short) when it pumps into the gap.
            setup["signal"] = "🔴 SELL"
            setup["logic"] = "Bearish FVG detected. Shorting the resistance."
            
            # SL goes just above the recent Swing High
            recent_highs = df[df['Swing_High'] == True]['High']
            setup["sl"] = recent_highs.iloc[-1] if not recent_highs.empty else current_price * 1.01
            
            # Calculate Risk to find the Take Profit
            risk = setup["sl"] - setup["entry"]
            setup["tp"] = setup["entry"] - (risk * reward_multiplier)

    # --- STRATEGY 2: BREAK & RETEST (Trend Following) ---
    elif "Break & Retest" in strategy:
        # Check if current price just broke above the last Swing High
        recent_highs = df[df['Swing_High'] == True]['High']
        if not recent_highs.empty and current_price > recent_highs.iloc[-1]:
            setup["signal"] = "🟢 BUY"
            setup["logic"] = "Resistance broken. Buying the retest of old resistance."
            
            setup["sl"] = recent_highs.iloc[-1] * 0.995 # SL just below the breakout line
            risk = setup["entry"] - setup["sl"]
            setup["tp"] = setup["entry"] + (risk * reward_multiplier)
            
    return setup