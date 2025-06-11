import requests
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime
import threading

print_lock = threading.Lock()  # For thread-safe console output
results=[]
def scrape_weather(city):
    city = city.lower().replace(" ", "-")
    url = f"https://www.timeanddate.com/weather/{city}"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # Temperature
        temp_div = soup.find("div", class_="h2")
        temperature = temp_div.text.strip() if temp_div else "N/A"

        # Condition
        condition_p = soup.find("p")
        condition = condition_p.text.strip() if condition_p else "N/A"

        # Details (Humidity, Dew Point, Pressure, Visibility)
        details = soup.find_all("table", class_="table table--left table--inner-borders-rows")

        humidity = pressure = dew_point = visibility = "N/A"
        if details:
            rows = details[0].find_all("tr")
            for row in rows:
                header = row.find("th")
                value = row.find("td")
                if header and value:
                    text = header.text.strip().lower()
                    val = value.text.strip()
                    if "humidity" in text:
                        humidity = val
                    elif "pressure" in text:
                        pressure = val
                    elif "dew point" in text:
                        dew_point = val
                    elif "visibility" in text:
                        visibility = val

        # Upcoming 5-hour forecast (if available)
        forecast_data = []
        forecast_table = soup.find("table", class_="zebra tb-wt fw va-m tb-hover")
        if forecast_table:
            rows = forecast_table.find_all("tr")[1:6]  # Get 5 rows
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    time = cols[0].text.strip()
                    forecast_condition = cols[1].text.strip()
                    forecast_data.append(f"{time}: {forecast_condition}")

        return {
            "city": city,
            "temperature": temperature,
            "condition": condition,
            "visibility": visibility,
            "pressure": pressure,
            "humidity": humidity,
            "dew_point": dew_point,
            "forecast": " | ".join(forecast_data) if forecast_data else "N/A",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": url
        }

    except Exception as e:
        with print_lock:
            print(f"[ERROR] Failed for {city}: {e}")
        return None

def log_to_csv(data, filename="weather_log.csv"):
    file_exists = os.path.isfile(filename)
    with open(filename, mode='a', newline='', encoding='utf-8-sig') as file:  # Changed to utf-8-sig
        writer = csv.DictWriter(file, fieldnames=data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

def process_city(city):
    result = scrape_weather(city)
    results.append(result)
   


def main(user_input):
    results.clear()
    cities = [c.strip() for c in user_input.split(",") if c.strip()]

    threads = []
    for city in cities:
     thread = threading.Thread(target=process_city, args=(city,))
     thread.start()
     threads.append(thread)

    for thread in threads:
        thread.join()
    return results     


