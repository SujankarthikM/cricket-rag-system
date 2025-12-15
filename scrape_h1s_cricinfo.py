

import requests
from bs4 import BeautifulSoup
import random
import time

class CricinfoH1Scraper:
    def __init__(self):
        self.session = requests.Session()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        ]
        self._set_headers()

    def _set_headers(self):
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        self.session.headers.update(headers)

    def scrape_h1s(self, url: str):
        time.sleep(random.uniform(1, 3))
        response = self.session.get(url, timeout=15)
        if response.status_code != 200:
            print(f"\n❌ Error: HTTP {response.status_code} for URL: {response.url}")
            url=response.url
            print('*'*100)
            print(response.text)

            last_part = url.rsplit("/", 1)[-1]
            name_only = last_part.rsplit("-", 1)[0]
            name = name_only.replace("-", " ")
            print(name)   # sachin-tendulkar
        soup = BeautifulSoup(response.content, 'html.parser')
        h1_tags = soup.find_all('h1')
        h1_texts = [h1.get_text(strip=True) for h1 in h1_tags]
        return h1_texts


if __name__ == "__main__":
    url = "https://stats.espncricinfo.com/ci/content/player/35320.html"
    scraper = CricinfoH1Scraper()
    h1s = scraper.scrape_h1s(url)

