import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"  # confirmed to support strict JSON-schema structured outputs


def analyze_sentiment_batch(headlines_list):
    if not headlines_list:
        return "[]"

    if not GROQ_API_KEY:
        print("❌ GROQ_API_KEY not set in .env — cannot call the LLM.")
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

    # THE IRON WALL: Strict JSON Schema (same guarantee the old Ollama
    # `format=schema` param gave us, now via Groq's structured outputs)
    json_schema = {
        "name": "headline_analysis",
        "strict": True,
        "schema": {
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
                        "required": ["headline", "sentiment", "confidence", "reasoning", "ticker"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["analyses"],
            "additionalProperties": False
        }
    }

    try:
        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
                "response_format": {"type": "json_schema", "json_schema": json_schema}
            },
            timeout=30
        )

        if response.status_code == 200:
            raw_response = response.json()["choices"][0]["message"]["content"]
            print(f"RAW GROQ OUTPUT:\n{raw_response}\n")

            try:
                data = json.loads(raw_response)
                analyses_array = data.get("analyses", [])
                return json.dumps(analyses_array)
            except json.JSONDecodeError:
                return "[]"
        else:
            print(f"GROQ API ERROR: {response.status_code} - {response.text[:300]}")
            return "[]"

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return "[]"
