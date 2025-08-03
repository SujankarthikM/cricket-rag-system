#!/usr/bin/env python3
"""
Reddit Cricket Discussion Scraper using RSS feeds
No authentication required - uses public RSS feeds
"""

import requests
import json
import time
from datetime import datetime
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import html

class RedditRSSCricketScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml',
        })
        self.scraped_data = []
        self.lock = Lock()
        
    def clean_text(self, text):
        """Clean text for RAG"""
        if not text:
            return ""
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove Reddit markup
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^\*]+)\*', r'\1', text)
        text = re.sub(r'~~([^~]+)~~', r'\1', text)
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'&gt;.*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'/u/\w+', '', text)
        text = re.sub(r'/r/\w+', '', text)
        text = re.sub(r'https?://\S+', '', text)
        
        # Clean whitespace
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text

    def is_substantial_discussion(self, title, description):
        """Check if post has substantial discussion content"""
        
        total_text = f"{title} {description}".strip()
        word_count = len(total_text.split())
        
        # Require substantial content
        if word_count < 40:
            return False
        
        # Avoid news/announcements
        avoid_keywords = [
            'breaking:', 'just in:', 'confirmed:', 'announced:', 'update:',
            'match thread', 'post match thread', 'live', 'scorecard',
            'highlights', 'squad announced', 'playing xi', 'injury',
            'toss', 'rain', 'weather', 'stumps'
        ]
        
        text_lower = total_text.lower()
        if any(keyword in text_lower for keyword in avoid_keywords):
            return False
        
        # Look for discussion indicators
        discussion_indicators = [
            'what do you think', 'opinion', 'debate', 'discuss', 'analysis',
            'breakdown', 'review', 'comparison', 'unpopular opinion', 'hot take',
            'why i think', 'personally', 'controversial', 'change my mind',
            'career analysis', 'performance review', 'tactical analysis',
            'statistical analysis', 'technique', 'strategy', 'detailed look',
            'comprehensive', 'in-depth', 'retrospective', 'perspective'
        ]
        
        if any(indicator in text_lower for indicator in discussion_indicators):
            return True
        
        # Long analytical posts
        if word_count > 100:
            analytical_patterns = [
                'analysis', 'breakdown', 'review', 'comparison',
                'statistical', 'tactical', 'performance', 'technique'
            ]
            if any(pattern in text_lower for pattern in analytical_patterns):
                return True
        
        return False

    def extract_post_id_from_url(self, url):
        """Extract Reddit post ID from URL"""
        match = re.search(r'/comments/([a-zA-Z0-9]+)/', url)
        return match.group(1) if match else None

    def fetch_rss_feed(self, url, feed_type):
        """Fetch and parse RSS feed"""
        try:
            print(f"📥 Fetching {feed_type} RSS feed...")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse XML
            root = ET.fromstring(response.content)
            
            # Find all entries
            entries = []
            
            # Handle both Atom and RSS formats
            if root.tag.endswith('feed'):  # Atom format
                for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry'):
                    title_elem = entry.find('.//{http://www.w3.org/2005/Atom}title')
                    content_elem = entry.find('.//{http://www.w3.org/2005/Atom}content')
                    link_elem = entry.find('.//{http://www.w3.org/2005/Atom}link')
                    author_elem = entry.find('.//{http://www.w3.org/2005/Atom}author/{http://www.w3.org/2005/Atom}name')
                    updated_elem = entry.find('.//{http://www.w3.org/2005/Atom}updated')
                    
                    if title_elem is not None:
                        entry_data = {
                            'title': title_elem.text or '',
                            'content': content_elem.text if content_elem is not None else '',
                            'link': link_elem.get('href') if link_elem is not None else '',
                            'author': author_elem.text if author_elem is not None else 'unknown',
                            'updated': updated_elem.text if updated_elem is not None else '',
                            'feed_type': feed_type
                        }
                        entries.append(entry_data)
            
            else:  # RSS format
                for item in root.findall('.//item'):
                    title_elem = item.find('title')
                    description_elem = item.find('description')
                    link_elem = item.find('link')
                    author_elem = item.find('author')
                    pubdate_elem = item.find('pubDate')
                    
                    if title_elem is not None:
                        entry_data = {
                            'title': title_elem.text or '',
                            'content': description_elem.text if description_elem is not None else '',
                            'link': link_elem.text if link_elem is not None else '',
                            'author': author_elem.text if author_elem is not None else 'unknown',
                            'updated': pubdate_elem.text if pubdate_elem is not None else '',
                            'feed_type': feed_type
                        }
                        entries.append(entry_data)
            
            print(f"✅ Found {len(entries)} entries from {feed_type}")
            return entries
            
        except Exception as e:
            print(f"❌ Error fetching {feed_type} RSS: {e}")
            return []

    def get_post_details_from_json(self, post_id):
        """Try to get additional post details using the .json endpoint"""
        try:
            url = f"https://www.reddit.com/r/cricket/comments/{post_id}.json"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0 and 'data' in data[0]:
                    post_data = data[0]['data']['children'][0]['data']
                    return {
                        'score': post_data.get('score', 0),
                        'num_comments': post_data.get('num_comments', 0),
                        'selftext': post_data.get('selftext', ''),
                        'flair': post_data.get('link_flair_text', ''),
                        'created_utc': post_data.get('created_utc', 0)
                    }
        except:
            pass
        return {}

    def process_rss_entry(self, entry):
        """Process a single RSS entry"""
        try:
            title = entry['title']
            description = entry['content']
            
            # Check if substantial discussion
            if not self.is_substantial_discussion(title, description):
                return None
            
            # Clean content
            clean_title = self.clean_text(title)
            clean_content = self.clean_text(description)
            total_content = f"{clean_title} {clean_content}"
            word_count = len(total_content.split())
            
            # Skip if cleaned content is too short
            if word_count < 30:
                return None
            
            # Extract post ID
            post_id = self.extract_post_id_from_url(entry['link'])
            
            # Try to get additional details (optional)
            extra_details = {}
            if post_id:
                extra_details = self.get_post_details_from_json(post_id)
                time.sleep(0.3)  # Small delay
            
            # Create entry
            post_entry = {
                'type': 'discussion_post',
                'id': post_id or f"rss_{hash(entry['link'])}",
                'title': clean_title,
                'content': total_content,
                'word_count': word_count,
                'author': entry['author'],
                'score': extra_details.get('score', 0),
                'num_comments': extra_details.get('num_comments', 0),
                'flair': extra_details.get('flair', ''),
                'link': entry['link'],
                'feed_type': entry['feed_type'],
                'updated': entry['updated'],
                'source': 'reddit_rss_cricket_discussion',
                'content_category': 'rss_discussion'
            }
            
            print(f"✅ {clean_title[:50]}... | {word_count} words | {entry['feed_type']}")
            return post_entry
            
        except Exception as e:
            print(f"❌ Error processing RSS entry: {e}")
            return None

    def scrape_cricket_discussions(self):
        """Scrape cricket discussions from RSS feeds"""
        
        print("🏏 Reddit Cricket RSS Discussion Scraper")
        print("📡 Using public RSS feeds (no authentication required)")
        print("🎯 Targeting substantial discussion content")
        print("=" * 60)
        
        # RSS feed URLs for r/cricket
        rss_feeds = [
            ('https://www.reddit.com/r/cricket.rss', 'recent'),
            ('https://www.reddit.com/r/cricket/hot.rss', 'hot'),
            ('https://www.reddit.com/r/cricket/top.rss?t=week', 'top_week'),
            ('https://www.reddit.com/r/cricket/top.rss?t=month', 'top_month'),
            ('https://www.reddit.com/r/cricket/top.rss?t=year', 'top_year'),
            ('https://www.reddit.com/r/cricket/top.rss?t=all', 'top_all'),
        ]
        
        all_entries = []
        
        # Fetch all RSS feeds
        for url, feed_type in rss_feeds:
            entries = self.fetch_rss_feed(url, feed_type)
            all_entries.extend(entries)
            time.sleep(1)  # Delay between feeds
        
        print(f"\n📊 Total RSS entries collected: {len(all_entries)}")
        
        # Remove duplicates based on link
        unique_entries = {}
        for entry in all_entries:
            link = entry['link']
            if link not in unique_entries:
                unique_entries[link] = entry
        
        print(f"📊 Unique entries after deduplication: {len(unique_entries)}")
        
        # Process entries with threading
        discussion_posts = []
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(self.process_rss_entry, entry) 
                      for entry in unique_entries.values()]
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        discussion_posts.append(result)
                except Exception as e:
                    print(f"❌ Thread error: {e}")
        
        return discussion_posts

    def save_dataset(self, data):
        """Save the RSS dataset"""
        if not data:
            print("❌ No data to save")
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"cricket_rss_discussions_{timestamp}.json"
        
        # Statistics
        total_words = sum(item['word_count'] for item in data)
        
        # Group by feed type
        feed_stats = {}
        for item in data:
            feed_type = item.get('feed_type', 'unknown')
            if feed_type not in feed_stats:
                feed_stats[feed_type] = 0
            feed_stats[feed_type] += 1
        
        dataset = {
            'metadata': {
                'source': 'reddit_r_cricket_rss',
                'content_type': 'rss_cricket_discussions',
                'scraping_method': 'rss_feeds_no_auth',
                'scraped_at': datetime.now().isoformat(),
                'total_posts': len(data),
                'total_words': total_words,
                'average_words_per_post': round(total_words / len(data), 1) if data else 0,
                'feed_breakdown': feed_stats,
                'quality_criteria': {
                    'minimum_words': 30,
                    'content_focus': 'discussions, analysis, opinions from RSS feeds',
                    'excluded_content': 'match threads, live updates, announcements',
                    'data_source': 'Reddit RSS feeds (public, no auth required)'
                }
            },
            'data': data
        }
        
        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        # Display results
        print(f"\n🎉 Cricket RSS Discussion Dataset Created!")
        print(f"=" * 50)
        print(f"📊 Total discussion posts: {len(data):,}")
        print(f"📝 Total words: {total_words:,}")
        print(f"📈 Average words per post: {dataset['metadata']['average_words_per_post']}")
        print(f"")
        print(f"📡 Feed breakdown:")
        for feed_type, count in feed_stats.items():
            print(f"   {feed_type}: {count} posts")
        print(f"")
        print(f"💾 File: {filename}")
        print(f"🎯 Ready for RAG: RSS-sourced cricket discussions!")
        
        return filename

def main():
    """Main execution"""
    scraper = RedditRSSCricketScraper()
    
    print("🚀 Starting Reddit RSS cricket discussion scraping...")
    print("📡 Using public RSS feeds - no authentication needed!")
    
    # Start scraping
    start_time = time.time()
    discussion_data = scraper.scrape_cricket_discussions()
    
    if discussion_data:
        # Save the dataset
        filename = scraper.save_dataset(discussion_data)
        
        elapsed_time = time.time() - start_time
        print(f"\n⏱️  Scraping completed in: {elapsed_time/60:.1f} minutes")
        
    else:
        print("❌ No discussion content found in RSS feeds")

if __name__ == "__main__":
    main()