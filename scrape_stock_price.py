import requests
from bs4 import BeautifulSoup
import threading
import time

# Example usage: AAPL, MSFT, GOOGL
example_input = "AAPL, MSFT, GOOGL"
print("Example stock symbols input:", example_input)


results = []
lock = threading.Lock()

def scrape_stock_price(stock_symbol, url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/90.0.4430.212 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://google.com'
    }

    try:
        print(f"Fetching {stock_symbol} data from {url}...")
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            result = {"symbol": stock_symbol, "source": url}

            if "yahoo.com" in url:
                price = soup.find("fin-streamer", {"data-field": "regularMarketPrice"})
                change = soup.find("fin-streamer", {"data-field": "regularMarketChange"})
                percent = soup.find("fin-streamer", {"data-field": "regularMarketChangePercent"})

                result["price"] = price.text if price else "N/A"
                result["change"] = change.text if change else "N/A"
                result["percent_change"] = percent.text if percent else "N/A"

            elif "marketwatch.com" in url:
                price = soup.find("bg-quote", class_="value")
                change = soup.find("bg-quote", class_="change--point--q")
                percent = soup.find("bg-quote", class_="change--percent--q")

                result["price"] = price.text.strip() if price else "N/A"
                result["change"] = change.text.strip() if change else "N/A"
                result["percent_change"] = percent.text.strip() if percent else "N/A"

            with lock:
                results.append(result)
                print(f"Successfully fetched {stock_symbol} data from {url}")
        else:
            print(f"Failed to fetch {url}. Status code: {response.status_code}")

    except Exception as e:
        print(f"Error fetching {stock_symbol} data from {url}: {e}")

def main(user_input):
    print("\nStarting stock price scraping...")
    results.clear()
    # Take user input for stock symbols
    symbols = [s.strip().upper() for s in user_input.split(',') if s.strip()]

# Generate stock URLs for each symbol
    stocks = [
        {"symbol": symbol, "urls": [
           f"https://finance.yahoo.com/quote/{symbol}",
           f"https://www.marketwatch.com/investing/stock/{symbol.lower()}"
     ]}
     for symbol in symbols
    ]

    threads = []

    for stock in stocks:
        for url in stock["urls"]:
            thread = threading.Thread(target=scrape_stock_price, args=(stock["symbol"], url))
            thread.start()
            threads.append(thread)
            time.sleep(0.5)  # Gentle delay to avoid hitting rate limits

    for thread in threads:
        thread.join()
    return results
