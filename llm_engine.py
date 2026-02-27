import json
import requests

def analyze_sentiment_batch(headlines_list):
    if not headlines_list:
        return "[]"

    headlines_text = "\n".join([f"- {h}" for h in headlines_list])
    
    prompt = f"""
    Analyze these financial headlines.
    Extract the exact sentiment, a confidence score (0-100), reasoning (max 7 words), and the main Yahoo Finance ticker symbol. If you don't know the ticker, use 'SPY'.
    
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