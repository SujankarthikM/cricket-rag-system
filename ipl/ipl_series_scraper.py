#!/usr/bin/env python3
"""
IPL Series Results Table Scraper
Scrapes links from the series results table on ESPNCricinfo IPL records page
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import time
from datetime import datetime
from urllib.parse import urljoin
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IPLSeriesScraper:
    def __init__(self):
        self.base_url = "https://www.espncricinfo.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.delay = 2  # Respectful delay
        
    def get_page(self, url, retries=3):
        """Fetch a page with error handling"""
        # First, visit main page to get cookies
        if not hasattr(self, '_cookies_set'):
            try:
                logger.info("Getting cookies from main page...")
                main_response = self.session.get("https://www.espncricinfo.com/", timeout=10)
                self._cookies_set = True
                time.sleep(1)
            except:
                pass
        
        for attempt in range(retries):
            try:
                logger.info(f"Fetching: {url} (Attempt {attempt + 1})")
                
                # Add referrer for this specific request
                headers = {
                    'Referer': 'https://www.espncricinfo.com/',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'same-origin',
                }
                
                response = self.session.get(url, timeout=15, headers=headers)
                
                logger.info(f"Status code: {response.status_code}")
                
                if response.status_code == 200:
                    time.sleep(self.delay)
                    return response
                elif response.status_code == 403:
                    logger.warning(f"403 Forbidden on attempt {attempt + 1}")
                
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
            if attempt == retries - 1:
                logger.error(f"Failed to fetch {url} after {retries} attempts")
                return None
            time.sleep(self.delay * (attempt + 1))
        return None

    def scrape_ipl_series_table(self):
        """Scrape the IPL series results table"""
        url = "https://www.espncricinfo.com/records/list-of-series-results-335432"
        response = self.get_page(url)
        
        if not response:
            logger.error("Failed to fetch IPL series page")
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all tables on the page
        tables = soup.find_all('table')
        logger.info(f"Found {len(tables)} tables on the page")
        
        all_links = []
        
        # Process each table
        for table_idx, table in enumerate(tables):
            logger.info(f"Processing table {table_idx + 1}")
            
            # Find all links within this table
            table_links = table.find_all('a', href=True)
            
            for link in table_links:
                href = link.get('href')
                text = link.get_text(strip=True)
                
                if href and text:
                    link_info = {
                        'text': text,
                        'url': urljoin(self.base_url, href),
                        'table_index': table_idx + 1,
                        'link_type': self.classify_link(href, text)
                    }
                    all_links.append(link_info)
        
        logger.info(f"Found {len(all_links)} total links in series tables")
        return all_links

    def classify_link(self, href, text):
        """Classify the type of link"""
        href_lower = href.lower()
        text_lower = text.lower()
        
        if '/series/' in href_lower:
            return 'series'
        elif '/team/' in href_lower:
            return 'team'
        elif '/player/' in href_lower:
            return 'player'
        elif 'season' in href_lower or 'season' in text_lower:
            return 'season'
        elif any(year in text for year in ['2008', '2009', '2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025']):
            return 'season_year'
        else:
            return 'other'

    def filter_series_links(self, all_links):
        """Filter to get only series-related links"""
        series_links = []
        
        for link in all_links:
            # Keep series links and season links
            if link['link_type'] in ['series', 'season', 'season_year']:
                series_links.append(link)
        
        logger.info(f"Filtered to {len(series_links)} series-related links")
        return series_links

    def save_links(self, links, filename_prefix):
        """Save links to JSON and CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save to JSON
        json_filename = f"{filename_prefix}_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(links, f, indent=2, ensure_ascii=False)
        
        # Save to CSV
        csv_filename = f"{filename_prefix}_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            if links:
                fieldnames = links[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(links)
        
        logger.info(f"Data saved to {json_filename} and {csv_filename}")
        return json_filename, csv_filename

def main():
    """Main function"""
    scraper = IPLSeriesScraper()
    
    print("🏏 IPL Series Results Table Scraper")
    print("=" * 50)
    
    # Scrape all links from tables
    all_links = scraper.scrape_ipl_series_table()
    
    if not all_links:
        print("❌ No links found")
        return
    
    # Filter for series links
    series_links = scraper.filter_series_links(all_links)
    
    # Save all links
    all_json, all_csv = scraper.save_links(all_links, "ipl_all_links")
    
    # Save series links
    series_json, series_csv = scraper.save_links(series_links, "ipl_series_links")
    
    # Print summary
    print(f"\n📊 Scraping Summary:")
    print(f"   Total links found: {len(all_links)}")
    print(f"   Series-related links: {len(series_links)}")
    
    # Show link type distribution
    link_types = {}
    for link in all_links:
        link_type = link['link_type']
        link_types[link_type] = link_types.get(link_type, 0) + 1
    
    print(f"\n📈 Link Type Distribution:")
    for link_type, count in sorted(link_types.items()):
        print(f"   {link_type}: {count}")
    
    # Show sample series links
    print(f"\n🔗 Sample Series Links:")
    for i, link in enumerate(series_links[:10]):
        print(f"   {i+1}. {link['text']} -> {link['url']}")
    
    print(f"\n💾 Files saved:")
    print(f"   All links: {all_json}, {all_csv}")
    print(f"   Series links: {series_json}, {series_csv}")

if __name__ == "__main__":
    main()