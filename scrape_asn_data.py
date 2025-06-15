import requests
from bs4 import BeautifulSoup
import threading




results=[]

def handle_single_asn(asn):
    print(f"Scanning {asn}...")
    try:
        # Send a GET request to the URL with the IP address
        url = f"https://ipinfo.io/AS{asn}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/90.0.4430.212 Safari/537.36'
        }
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            
            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')

            result = {}
            result['asn'] = f"AS{asn}"  # Store ASN

            # === Geolocation Block ===
            geo_block = soup.find('div', id='block-geolocation')
            if geo_block:
                table = geo_block.find('table')
                if table:
                    for row in table.find_all('tr'):
                        cells = row.find_all('td')
                        if len(cells) == 2:
                            key = cells[0].get_text(strip=True)
                            value = cells[1].get_text(strip=True)
                            result[key] = value

            # === Summary Block ===
            summary_block = soup.find('div', id='block-summary')
            if summary_block:
                summary_table = summary_block.find('table')
                if summary_table:
                    for row in summary_table.find_all('tr'):
                        cells = row.find_all('td')
                        if len(cells) == 2:
                            key = cells[0].get_text(strip=True)
                            value_cell = cells[1]

                            # Handle links in the value cell
                            link = value_cell.find('a')
                            if link:
                                link_text = link.get_text(strip=True)
                                link_href = link.get('href')
                                value = f"{link_text} ({link_href})" if link_href else link_text
                            else:
                                value = value_cell.get_text(strip=True)

                            result[key] = value

            
            results.append(result)       
        else:
            print(f"asn: {asn}, Status Code: {response.status_code}")

    except requests.RequestException as e:
        print(f"asn: {asn}, Error: {e}")


def main(input):
    # Create a list of IP addresses in the subnet
    results.clear()
    start_str, end_str = input.split('-')
    start = int(start_str)
    end = int(end_str)

# Generate the list of strings
    asn_list = [str(i) for i in range(start, end + 1)]

    threads = []
    for i in asn_list:
        
        thread = threading.Thread(target=handle_single_asn, args=(i,))
        threads.append(thread)
        thread.start()

     # Now wait for all threads to finish
    for thread in threads:
        thread.join()
    print(results);        
    return results

