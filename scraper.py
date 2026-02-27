import requests
from bs4 import BeautifulSoup
import warnings
from bs4 import XMLParsedAsHTMLWarning

# This hides that annoying yellow warning message!
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

def fetch_financial_news():
    url = "https://news.google.com/rss/search?q=stock+market+finance+tech&hl=en-US&gl=US&ceid=US:en"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print("🤖 Agent initiating web scrape...")
    print("Fetching live news headlines...\n")
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    items = soup.find_all("item")
    
    news_list = []
    
    for item in items[:100]: 
        headline = item.title.text
        news_list.append(headline)
        print(f"📰 {headline}")
        
    print("\n✅ Scrape complete. Data ready for Sentiment Analysis.")
    return news_list

if __name__ == "__main__":
    fetch_financial_news()