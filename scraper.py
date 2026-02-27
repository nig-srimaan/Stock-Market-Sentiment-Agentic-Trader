import requests
from bs4 import BeautifulSoup
import warnings
from bs4 import XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

def fetch_financial_news(count=15):
    # UPGRADED URL: Now searches Indian Markets + Global Equities!
    url = "https://news.google.com/rss/search?q=(NSE+OR+BSE+OR+Nifty+OR+Sensex+OR+stock+market)+when:1d&hl=en-IN&gl=IN&ceid=IN:en"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.content, "html.parser") 
        items = soup.find_all("item")
        
        news_list = []
        for item in items[:count]:
            title = item.title.text.rsplit(' - ', 1)[0]
            news_list.append(title)
            
        if not news_list:
            raise ValueError("Feed empty")
            
        return news_list
        
    except Exception as e:
        print(f"⚠️ Scraper blocked. Using Global/Indian Fail-Safe data...")
        
        # OFFLINE FALLBACK: Mix of NSE and Global stocks
        fallback_news = [
            "Reliance Industries (RELIANCE) announces massive 5G expansion, stock surges",
            "Tata Motors (TATAMOTORS) reports record EV sales this quarter",
            "Nvidia (NVDA) hits new all-time high on AI chip demand",
            "Infosys (INFY) faces unexpected headwinds in US markets",
            "HDFC Bank (HDFCBANK) quarterly earnings beat Dalal Street expectations",
            "Nifty 50 (^NSEI) closes at record high amidst bullish global cues"
        ]
        
        while len(fallback_news) < count:
            fallback_news.extend(fallback_news)
            
        return fallback_news[:count]