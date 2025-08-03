import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import re

def load_links_from_json(filename='kingcricket_continue_links.json'):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [item['url'] for item in data]
    except Exception as e:
        print(f"Error loading links from {filename}: {str(e)}")
        return []

def extract_date_from_url(url):
    date_pattern = r'/(\d{4})/(\d{2})/(\d{2})/'
    match = re.search(date_pattern, url)
    if match:
        year, month, day = match.groups()
        return f"{year}-{month}-{day}"
    return None

def scrape_article_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title = soup.find('h1')
        title_text = title.get_text(strip=True) if title else ""
        
        paragraphs = []
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if text and len(text) > 20:
                paragraphs.append(text)
        
        content = '\n\n'.join(paragraphs)
        article_date = extract_date_from_url(url)
        
        return {
            'url': url,
            'title': title_text,
            'content': content,
            'content_length': len(content),
            'article_date': article_date,
            'scraped_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return None

def scrape_articles_parallel(urls, max_workers=10):
    articles = []
    
    def scrape_with_progress(url):
        article = scrape_article_content(url)
        if article:
            print(f"Successfully scraped: {article['title'][:50]}...")
        return article
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(scrape_with_progress, url): url for url in urls}
        
        for future in as_completed(future_to_url):
            article = future.result()
            if article:
                articles.append(article)
    
    return articles

def save_to_json(data, filename='kingcricket_articles.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    print("Loading article URLs from kingcricket_continue_links.json...")
    urls = load_links_from_json()
    
    if not urls:
        print("No URLs found. Make sure kingcricket_continue_links.json exists.")
        exit()
    
    print(f"Found {len(urls)} article URLs to scrape")
    
    # Scrape all articles with multithreading
    articles = scrape_articles_parallel(urls, max_workers=15)
    
    print(f"Successfully scraped {len(articles)} articles")
    
    save_to_json(articles)
    print(f"Saved {len(articles)} articles to kingcricket_articles.json")