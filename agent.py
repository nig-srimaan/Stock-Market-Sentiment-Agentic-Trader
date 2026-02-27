from scraper import fetch_financial_news
from llm_engine import analyze_sentiment_batch
import json

def run_trading_agent():
    print("🚀 Starting Enterprise Stock Market Sentiment Agent...\n")
    
    # 1. Grab a massive list of news (Make sure scraper.py is set to grab 50 or 100!)
    headlines = fetch_financial_news()
    
    if not headlines:
        print("❌ No headlines found. Exiting.")
        return

    # 2. Send the ENTIRE list to the AI in one single API call
    try:
        ai_verdict_json = analyze_sentiment_batch(headlines)
        
        # Convert the AI's text response back into a Python list
        verdicts = json.loads(ai_verdict_json)
        
        print(f"\n✅ Successfully analyzed {len(verdicts)} headlines instantly!\n")
        
        # Print them out beautifully
        for item in verdicts:
            print(f"📰 {item['headline']}")
            print(f"🤖 {item['sentiment']} ({item['confidence']}%) - {item['reasoning']}")
            print("-" * 80)
            
    except Exception as e:
        print(f"⚠️ Agent encountered an error: {e}")
        print("Raw output for debugging:", ai_verdict_json)

if __name__ == "__main__":
    run_trading_agent()