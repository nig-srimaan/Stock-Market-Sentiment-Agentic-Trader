import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

# --- DEV 1'S FUNCTION (For the News Scraper) ---
def analyze_sentiment_batch(headlines_list):
    print(f"🧠 Sending a batch of {len(headlines_list)} headlines to the AI for parallel processing...")
    headlines_text = "\n".join([f"- {h}" for h in headlines_list])
    
    prompt = f"""
    Act as an expert stock market algorithmic trader. 
    Analyze this list of financial news headlines:
    {headlines_text}
    
    Determine if the sentiment is Bullish, Bearish, or Neutral for the overall stock market.
    Respond with ONLY a valid JSON array. Do not include markdown formatting like ```json.
    
    Format EXACTLY like this:
    [
        {{"headline": "The exact headline text", "sentiment": "Bullish", "confidence": 85, "reasoning": "Short reason."}}
    ]
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    clean_text = response.text.strip().removeprefix('```json').removesuffix('```').strip()
    return clean_text


# --- DEV 2'S FUNCTION (For the Dashboard UI Text Box) ---
def analyze_news_sentiment(news_headline):
    print(f"🤖 AI Analyzing Single Headline: {news_headline}")
    
    prompt = f"""
    Act as an expert stock market algorithmic trader. Analyze this financial news headline:
    "{news_headline}"
    
    Determine the market sentiment and output a trading decision.
    Respond ONLY with a valid JSON object in this exact format, with no other text:
    {{"action": "BUY" or "SELL" or "HOLD", "ticker": "STOCK_TICKER", "confidence": 85}}
    
    If no specific stock is mentioned, use "NONE" for the ticker and "HOLD" for the action.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        clean_text = response.text.strip().removeprefix('```json').removesuffix('```').strip()
        return json.loads(clean_text)
    except Exception as e:
        print(f"🔴 AI Brain Error: {e}")
        return {"action": "HOLD", "ticker": "ERROR", "confidence": 0}