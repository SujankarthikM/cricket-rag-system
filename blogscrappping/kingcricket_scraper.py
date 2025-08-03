import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_continue_reading_links(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        continue_links = []
        
        # Find all links with "Continue reading" text
        for a_tag in soup.find_all('a', href=True):
            text = a_tag.get_text(strip=True)
            if 'continue reading' in text.lower():
                href = a_tag['href']
                
                # Ensure full URL
                if href.startswith('/'):
                    href = 'https://www.kingcricket.co.uk' + href
                
                continue_links.append({
                    'url': href,
                    'text': text,
                    'scraped_at': datetime.now().isoformat()
                })
        
        return continue_links
        
    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return []

def get_all_pages_links(base_url, max_pages=200):
    all_links = []
    
    def scrape_page(page):
        url = f"{base_url}/page/{page}/"
        print(f"Scraping page {page}: {url}")
        return get_continue_reading_links(url)
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_page = {executor.submit(scrape_page, page): page for page in range(1, max_pages + 1)}
        
        for future in as_completed(future_to_page):
            page = future_to_page[future]
            try:
                page_links = future.result()
                if page_links:
                    all_links.extend(page_links)
                    print(f"Page {page}: Found {len(page_links)} links")
                else:
                    print(f"Page {page}: No links found")
            except Exception as e:
                print(f"Page {page} failed: {str(e)}")
    
    return all_links

def save_to_json(data, filename='kingcricket_continue_links.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    base_url = "https://www.kingcricket.co.uk"
    print(f"Scraping 'Continue reading' links from: {base_url}")
    
    all_links = get_all_pages_links(base_url)
    
    # Remove duplicates
    unique_links = []
    seen_urls = set()
    for link in all_links:
        if link['url'] not in seen_urls:
            unique_links.append(link)
            seen_urls.add(link['url'])
    
    print(f"Found {len(unique_links)} unique 'Continue reading' links")
    
    save_to_json(unique_links)
    print(f"Saved {len(unique_links)} links to kingcricket_continue_links.json")