import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load the secret key from the .env file
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

def analyze_news_sentiment(news_headline):
    # Dev 1 will put the real AI Prompt logic here later!
    # For now, it just pretends to work so Dev 2 can test the UI.
    
    print(f"🤖 AI Analyzing: {news_headline}")
    
    # Fake logic just for UI testing:
    if "Apple" in news_headline or "Bullish" in news_headline:
        return {"action": "BUY", "ticker": "AAPL", "confidence": 85}
    elif "Tesla" in news_headline or "Crash" in news_headline:
        return {"action": "SELL", "ticker": "TSLA", "confidence": 90}
    else:
        return {"action": "HOLD", "ticker": "NONE", "confidence": 0}