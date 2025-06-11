import requests
from bs4 import BeautifulSoup
import threading




results=[]

def handle_single_ip(ip):
    print(f"Scanning {ip}...")
    try:
        # Send a GET request to the URL with the IP address
        url = f"https://ipinfo.io/{ip}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/90.0.4430.212 Safari/537.36'
        }
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            
            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            result={}
            result['ip'] = ip
            # Extract the ip data
            geo_block=soup.find('div',id='block-geolocation')
            table=geo_block.find('table')
            
              # Iterate through all rows
            for row in table.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) == 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    result[key] = value
            
            summary_block = soup.find('div', id='block-summary')
            if summary_block:
                summary_table = summary_block.find('table')
                if summary_table:
                    for row in summary_table.find_all('tr'):
                        cells = row.find_all('td')
                        if len(cells) == 2:
                            key = cells[0].get_text(strip=True)
                            # Extract text **and** any link (if present)
                            value_cell = cells[1]

                            # If cell contains <a>, get link text + href
                            link = value_cell.find('a')
                            if link:
                                link_text = link.get_text(strip=True)
                                link_href = link.get('href')
                                value = f"{link_text} ({link_href})" if link_href else link_text
                            else:
                                value = value_cell.get_text(strip=True)

                            result[key] = value

            print(result)
            results.append(result);        
        else:
            print(f"IP: {ip}, Status Code: {response.status_code}")

    except requests.RequestException as e:
        print(f"IP: {ip}, Error: {e}")


def main(subnet):
    # Create a list of IP addresses in the subnet
    results.clear()
    ip_list = [f"{subnet}.{i}" for i in range(1, 20)]
    
    threads = []
    for i in ip_list:
        
        thread = threading.Thread(target=handle_single_ip, args=(i,))
        threads.append(thread)
        thread.start()

     # Now wait for all threads to finish
    for thread in threads:
        thread.join()    
    return results


# handle_single_ip("68.248.195.100")