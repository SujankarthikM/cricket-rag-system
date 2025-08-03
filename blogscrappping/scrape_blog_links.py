import requests
from bs4 import BeautifulSoup
import re
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_blog_links(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    blog_links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        text = link.get_text(strip=True)
        
        if 'blog' in href.lower() or 'blog' in text.lower():
            if href.startswith('/'):
                href = 'https://mysterycricket.com' + href
            blog_links.append({'url': href, 'text': text})
    
    return blog_links

def scrape_blog_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title = soup.find('h1')
        title_text = title.get_text(strip=True) if title else ""
        
        sections = []
        current_section = {"heading": "", "content": []}
        
        all_elements = soup.find_all(['h2', 'p'])
        
        for element in all_elements:
            if element.name == 'h2':
                if current_section["heading"] or current_section["content"]:
                    sections.append(current_section)
                current_section = {"heading": element.get_text(strip=True), "content": []}
            elif element.name == 'p':
                text = element.get_text(strip=True)
                if text and len(text) > 20:
                    current_section["content"].append(text)
        
        if current_section["heading"] or current_section["content"]:
            sections.append(current_section)
        
        author_meta = soup.find('script', type='application/ld+json')
        author = ""
        if author_meta:
            try:
                json_data = json.loads(author_meta.string)
                author = json_data.get('author', {}).get('name', '')
            except:
                pass
        
        return {
            'url': url,
            'title': title_text,
            'author': author,
            'sections': sections,
            'scraped_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return None

def save_to_json(data, filename='cricket_blog_data.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    print("Getting all blog links...")
    all_links = []
    for i in range(1, 9):
        url = f"https://mysterycricket.com/blogs/the-mystery-cricket-blog?page={i}"
        links = get_blog_links(url)
        req = [x['url'] for x in links if '/blogs/' in x['url']]
        req = [x['url'] for x in links if 'page' not in x['url']]
        all_links.extend(req)

    
    all_links = list(set(all_links))
    print(f"Found {len(all_links)} unique blog posts")
    
    blog_data = []
    
    def scrape_with_progress(link):
        content = scrape_blog_content(link)
        if content:
            print(f"Successfully scraped: {content['title']}")
        return content
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(scrape_with_progress, link): link for link in all_links}
        
        for future in as_completed(future_to_url):
            content = future.result()
            if content:
                blog_data.append(content)
    
    save_to_json(blog_data)
    print(f"Saved {len(blog_data)} blog posts to cricket_blog_data.json")



