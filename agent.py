from scraper import fetch_financial_news
from llm_engine import analyze_sentiment_batch
import json

def run_trading_agent():
    print("🚀 Starting Enterprise Stock Market Sentiment Agent...\n")
    
    headlines, is_fallback = fetch_financial_news(count=50) # Set a default count
    
    if not headlines:
        print("❌ No headlines found. Exiting.")
        return

    if is_fallback:
        print("⚠️ Running on FALLBACK data (live scrape failed) — not live headlines.\n")

    ai_verdict_json = "[]" # Initialize this so it doesn't crash the except block
    
    try:
        ai_verdict_json = analyze_sentiment_batch(headlines)
        verdicts = json.loads(ai_verdict_json)
        
        if len(verdicts) == 0:
            print("⚠️ AI returned empty analysis.")
            return

        print(f"\n✅ Successfully analyzed {len(verdicts)} headlines instantly!\n")
        
        for item in verdicts:
            # Using .get() prevents KeyError if the AI hallucinates a column name
            sentiment = item.get('sentiment', 'Unknown')
            confidence = item.get('confidence', 0)
            reasoning = item.get('reasoning', 'No reason provided')
            
            print(f"📰 {item.get('headline', 'Unknown Headline')}")
            print(f"🤖 {sentiment} ({confidence}%) - {reasoning}")
            print("-" * 80)
            
    except Exception as e:
        print(f"⚠️ Agent encountered an error: {e}")
        print("Raw output for debugging:", ai_verdict_json)

if __name__ == "__main__":
    run_trading_agent()
