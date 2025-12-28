"""
FINANCIAL NEWS AGGREGATOR - REFERENCE VERSION
Target: Yahoo Finance API (yfinance)
Goal: Fetch, clean, and chronologically sort market news for a watchlist.
"""

import yfinance as yf
from datetime import datetime

# 1. WATCHLIST DEFINITION
# We use a Dictionary {Key: Value} for O(1) lookup speed.
# Key = Friendly Name, Value = Ticker symbol used by the API.
# Note: Commodities like Gold/Silver use "=F" (Futures) suffixes in Yahoo Finance.
watchlist = {
    "Google": "GOOGL",
    "Tesla": "TSLA",
    "Palantir": "PLTR",
    "Nvidia": "NVDA",
    "Gold": "GC=F",
    "Silver": "SI=F"
}

def get_news(name, ticker):
    """
    Fetches and sanitizes news data for a single ticker.
    Handles the 'messy' nature of API responses where keys might change.
    """
    print(f"Fetching news for {name} ({ticker})....")
    
    # Initialize the Ticker object. This doesn't download data yet; 
    # it just creates a Python object linked to that symbol.
    data = yf.Ticker(ticker)
    
    # .news is a property that returns a list of dictionaries.
    # If the API is down or the ticker is invalid, this might be empty.
    newslist = data.news
    
    if not newslist:
        return [] # Return empty list to prevent the main loop from crashing
    
    cleaned_news = []
    
    # Iterate through every 'story' (which is a dictionary) provided by the API
    for story in newslist:
        
        # --- TIMESTAMP EXTRACTION (The Hard Part) ---
        # APIs change their schema often. We use 'story.get()' instead of story['key'].
        # .get() is safer because if the key is missing, it returns None instead of crashing.
        # We try three different possible locations for the timestamp:
        raw_time = (
            story.get("providerPublishTime") or 
            story.get("pubDate") or 
            story.get("content", {}).get("pubDate") # Nested lookup
        )
        
        time_str = "Unknown Time"
        
        try:
            # Check if the time is a Unix Timestamp (e.g., 1710921600)
            if isinstance(raw_time, (int, float)):
                # datetime.fromtimestamp converts seconds since 1970 into a readable object
                dt_object = datetime.fromtimestamp(raw_time)
                # .strftime formats the object into a string (Year-Month-Day Hour:Min:Sec)
                time_str = dt_object.strftime("%Y-%m-%d %H:%M:%S")
            
            # Check if the time is an ISO String (e.g., "2024-03-20T10:00:00Z")
            elif isinstance(raw_time, str):
                # Replace 'Z' (Zulu/UTC) with a Python-friendly offset (+00:00)
                # fromisoformat() is a built-in fast parser for standard date strings
                dt_object = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
                time_str = dt_object.strftime("%Y-%m-%d %H:%M:%S")
        
        except Exception:
            # If parsing fails (e.g., weird characters), fallback to raw data
            time_str = str(raw_time) if raw_time else "Unknown Time"

        # --- HEADLINE EXTRACTION ---
        # Again, we check top-level "title" OR inside a "content" sub-dictionary.
        headline = story.get("title") or story.get("content", {}).get("title", "No Title")
        
        # --- DATA NORMALIZATION ---
        # We create our own 'clean' dictionary so every news item looks exactly the same,
        # regardless of how messy the original API response was.
        info = {
            "company": name,
            "ticker": ticker,
            "headline": headline,
            "time": time_str
        }
        cleaned_news.append(info)
        
    return cleaned_news

# --- MAIN EXECUTION FLOW ---

# 1. Create a master list to hold all news from all companies
all_market_news = [] 

# 2. Loop through the watchlist. .items() gives us both the Name and the Ticker.
for name, ticker in watchlist.items():
    try:
        # Fetch the cleaned list for this specific stock
        results = get_news(name, ticker)
        # .extend() adds the ELEMENTS of the list to the master list (unlike .append which adds the list itself)
        all_market_news.extend(results)
    except Exception as e:
        # Crucial for Quants: If one ticker fails, don't let the whole program die.
        print(f"Error on {ticker}: {e}")

# 3. GLOBAL SORTING
# We want the most recent news at the top. 
# key=lambda x: x['time'] tells Python: "Sort based on the 'time' value inside each dictionary."
# reverse=True means Descending order (Newest -> Oldest).
all_market_news.sort(key=lambda x: x['time'], reverse=True)

# 4. FINAL DISPLAY
print("\n" + "="*80)
print(f"{'TIMESTAMP':<20} | {'TICKER':<10} | {'HEADLINE'}")
print("-" * 80)

for item in all_market_news:
    # item['company']:<10 means "Left align the company name within 10 spaces"
    print(f"[{item['time']}] {item['company']:<10} | {item['headline']}")
