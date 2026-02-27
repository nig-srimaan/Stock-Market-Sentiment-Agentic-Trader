import json
import requests

def analyze_sentiment_batch(headlines_list):
    if not headlines_list:
        return "[]"

    headlines_text = "\n".join([f"- {h}" for h in headlines_list])
    
    prompt = f"""
    Analyze these financial headlines.
    Extract the sentiment, a confidence score (0-100), reasoning (max 7 words), and the Yahoo Finance ticker symbol. 
    
    CRITICAL TICKER RULES:
    1. If it is an Indian company, you MUST append '.NS' to the ticker (e.g., RELIANCE.NS, TATAMOTORS.NS, HDFCBANK.NS, INFY.NS).
    2. If it's a US company, leave it normal (e.g., NVDA, AAPL).
    3. If it's general Indian market news, use '^NSEI' (The Nifty 50 Index).
    4. If you absolutely don't know, use 'SPY'.
    
    Headlines:
    {headlines_text}
    """
    
    # 🧱 THE IRON WALL: Strict JSON Schema
    schema = {
        "type": "object",
        "properties": {
            "analyses": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "headline": {"type": "string"},
                        "sentiment": {"type": "string", "enum": ["Bullish", "Bearish", "Neutral"]},
                        "confidence": {"type": "integer"},
                        "reasoning": {"type": "string"},
                        "ticker": {"type": "string"}
                    },
                    "required": ["headline", "sentiment", "confidence", "reasoning", "ticker"]
                }
            }
        },
        "required": ["analyses"]
    }
    
    try:
        response = requests.post('http://localhost:11434/api/generate', json={
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False,
            "format": schema,
            "options": {"temperature": 0.0} 
        }, timeout=300) 
        
        if response.status_code == 200:
            raw_response = response.json().get("response", "")
            print(f"🤖 RAW OLLAMA OUTPUT:\n{raw_response}\n")
            
            try:
                data = json.loads(raw_response)
                analyses_array = data.get("analyses", [])
                return json.dumps(analyses_array)
            except json.JSONDecodeError:
                return "[]"
        else:
            print(f"❌ OLLAMA API ERROR: {response.status_code}")
            return "[]"
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        return "[]"