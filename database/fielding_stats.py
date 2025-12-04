
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin

def scrape_fielding_stats(url):
    """
    Scrapes fielding stats from the given URL.
    """
    import time
    max_retries = 10
    delay = 2
    for attempt in range(max_retries):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            tables = soup.find_all('table', class_='engineTable')
            if not tables:
                return {}
            table = tables[2]
            import re
            results = {}
            for row in table.find('tbody').find_all('tr'):
                try:
                    first_td = row.find('td')
                    if first_td:
                        a_tag = first_td.find('a')
                        value = a_tag.get_text(strip=True) if a_tag else first_td.get_text(strip=True)
                        link = urljoin(url, a_tag['href']) if a_tag and a_tag.has_attr('href') else None
                        if link:
                            player_id = re.findall(r'(\d+)(?=\.html$)', link)[0]
                            if player_id not in results:
                                results[player_id] = value
                except Exception:
                    continue
            return results
        except requests.exceptions.RequestException:
            time.sleep(delay)
            continue
    return {}

if __name__ == '__main__':
    
    import csv
    all_results = {}
    for x in range(1, 41):
        print(f"Page:{x}")
        url = f"https://stats.espncricinfo.com/ci/engine/stats/index.html?class=11;filter=advanced;orderby=matches;page={x};size=200;template=results;type=fielding"
        res = scrape_fielding_stats(url)
        if res:
            all_results.update(res)

    for x in range(1, 5):
        url = f"https://stats.espncricinfo.com/ci/engine/stats/index.html?class=6;filter=advanced;orderby=matches;page={x};size=200;template=results;trophy=117;type=fielding"
        res = scrape_fielding_stats(url)
        if res:
            all_results.update(res)

    with open('unique_fielding_players.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Player Name', 'Player ID'])
        for player_id, value in all_results.items():
            writer.writerow([value, player_id])
    from concurrent.futures import ThreadPoolExecutor, as_completed

    urls = []
    for x in range(1, 41):
        print(f"Page:{x}")
        urls.append(f"https://stats.espncricinfo.com/ci/engine/stats/index.html?class=11;filter=advanced;orderby=matches;page={x};size=200;template=results;type=fielding")
    for x in range(1, 5):
        urls.append(f"https://stats.espncricinfo.com/ci/engine/stats/index.html?class=6;filter=advanced;orderby=matches;page={x};size=200;template=results;trophy=117;type=fielding")

    all_results = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_url = {executor.submit(scrape_fielding_stats, url): url for url in urls}
        for future in as_completed(future_to_url):
            res = future.result()
            if res:
                all_results.update(res)

    with open('unique_fielding_players.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Player Name', 'Player ID'])
        for player_id, value in all_results.items():
            writer.writerow([value, player_id])