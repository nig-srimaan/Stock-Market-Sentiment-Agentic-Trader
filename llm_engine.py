import os
from google import genai
from dotenv import load_dotenv
import json

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

def analyze_sentiment_batch(headlines_list):
    print(f"🧠 Sending a batch of {len(headlines_list)} headlines to the AI for parallel processing...")
    
    # We turn the Python list into a single text string for the AI to read
    headlines_text = "\n".join([f"- {h}" for h in headlines_list])
    
    prompt = f"""
    Act as an expert stock market algorithmic trader. 
    Analyze this list of financial news headlines:
    
    {headlines_text}
    
    Determine if the sentiment is Bullish, Bearish, or Neutral for the overall stock market.
    Respond with ONLY a valid JSON array. Do not include markdown formatting like ```json.
    
    Format EXACTLY like this:
    [
        {{"headline": "The exact headline text", "sentiment": "Bullish", "confidence": 85, "reasoning": "Short reason."}},
        {{"headline": "The exact headline text", "sentiment": "Bearish", "confidence": 90, "reasoning": "Short reason."}}
    ]
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    
    # Clean the response just in case the AI adds markdown blocks
    clean_text = response.text.strip().removeprefix('```json').removesuffix('```').strip()
    return clean_text