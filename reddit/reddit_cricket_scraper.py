#!/usr/bin/env python3
"""
Reddit Cricket Scraper
Scrapes cricket-related posts and comments from r/cricket subreddit
"""

import requests
import json
import csv
import time
from datetime import datetime, timezone
import logging
from pathlib import Path
import re
from urllib.parse import urljoin
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RedditCricketScraper:
    def __init__(self):
        self.base_url = "https://www.reddit.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CricketBot/1.0 (Educational Research Project)',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        self.delay = 2  # Respectful delay between requests
        self.lock = Lock()
        self.max_workers = 5  # Conservative threading for Reddit
        self.scraped_count = 0
        
    def get_page(self, url, retries=3):
        """Fetch a page with error handling"""
        for attempt in range(retries):
            try:
                logger.info(f"Fetching: {url} (Attempt {attempt + 1})")
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    time.sleep(self.delay)  # Respectful delay
                    return response
                elif response.status_code == 429:  # Rate limited
                    wait_time = self.delay * (attempt + 1) * 2
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.warning(f"Status code {response.status_code} for {url}")
                
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                
            if attempt == retries - 1:
                logger.error(f"Failed to fetch {url} after {retries} attempts")
                return None
            time.sleep(self.delay * (attempt + 1))
        return None

    def scrape_subreddit_posts(self, subreddit="cricket", limit=100, sort="hot"):
        """Scrape posts from r/cricket subreddit"""
        posts_data = []
        
        # Reddit JSON API endpoint
        url = f"https://www.reddit.com/r/{subreddit}/{sort}.json?limit={limit}"
        
        response = self.get_page(url)
        if not response:
            logger.error(f"Failed to fetch r/{subreddit}")
            return []

        try:
            data = response.json()
            posts = data['data']['children']
            
            logger.info(f"Found {len(posts)} posts in r/{subreddit}")
            
            for post in posts:
                post_data = post['data']
                
                # Extract post information
                post_info = {
                    'id': post_data.get('id'),
                    'title': post_data.get('title', ''),
                    'selftext': post_data.get('selftext', ''),
                    'author': post_data.get('author', '[deleted]'),
                    'score': post_data.get('score', 0),
                    'upvote_ratio': post_data.get('upvote_ratio', 0),
                    'num_comments': post_data.get('num_comments', 0),
                    'created_utc': post_data.get('created_utc', 0),
                    'created_date': datetime.fromtimestamp(post_data.get('created_utc', 0), tz=timezone.utc).isoformat(),
                    'url': post_data.get('url', ''),
                    'permalink': f"https://www.reddit.com{post_data.get('permalink', '')}",
                    'subreddit': post_data.get('subreddit', ''),
                    'flair_text': post_data.get('link_flair_text', ''),
                    'is_self': post_data.get('is_self', False),
                    'domain': post_data.get('domain', ''),
                    'content_type': 'post',
                    'scraped_at': datetime.now().isoformat()
                }
                
                # Clean and process text content
                post_info['full_text'] = self.clean_text(f"{post_info['title']} {post_info['selftext']}")
                post_info['word_count'] = len(post_info['full_text'].split()) if post_info['full_text'] else 0
                
                posts_data.append(post_info)
                
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Error parsing Reddit JSON: {e}")
            return []
        
        return posts_data

    def scrape_post_comments(self, post_id, limit=50):
        """Scrape comments from a specific post"""
        comments_data = []
        
        # Reddit JSON API for comments
        url = f"https://www.reddit.com/comments/{post_id}.json?limit={limit}"
        
        response = self.get_page(url)
        if not response:
            logger.warning(f"Failed to fetch comments for post {post_id}")
            return []

        try:
            data = response.json()
            
            # Comments are in the second element of the response
            if len(data) > 1 and 'data' in data[1]:
                comments = data[1]['data']['children']
                
                for comment in comments:
                    if comment['kind'] == 't1':  # Comment type
                        comment_data = comment['data']
                        
                        comment_info = {
                            'id': comment_data.get('id'),
                            'post_id': post_id,
                            'body': comment_data.get('body', ''),
                            'author': comment_data.get('author', '[deleted]'),
                            'score': comment_data.get('score', 0),
                            'created_utc': comment_data.get('created_utc', 0),
                            'created_date': datetime.fromtimestamp(comment_data.get('created_utc', 0), tz=timezone.utc).isoformat(),
                            'permalink': f"https://www.reddit.com{comment_data.get('permalink', '')}",
                            'parent_id': comment_data.get('parent_id', ''),
                            'depth': comment_data.get('depth', 0),
                            'content_type': 'comment',
                            'scraped_at': datetime.now().isoformat()
                        }
                        
                        # Clean text and count words
                        comment_info['clean_text'] = self.clean_text(comment_info['body'])
                        comment_info['word_count'] = len(comment_info['clean_text'].split()) if comment_info['clean_text'] else 0
                        
                        # Only include substantial comments
                        if comment_info['word_count'] > 5:
                            comments_data.append(comment_info)
                
        except (KeyError, json.JSONDecodeError, IndexError) as e:
            logger.warning(f"Error parsing comments for post {post_id}: {e}")
            return []
        
        return comments_data

    def clean_text(self, text):
        """Clean Reddit text content"""
        if not text:
            return ""
        
        # Remove Reddit markup
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Remove markdown links
        text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)  # Remove bold
        text = re.sub(r'\*([^\*]+)\*', r'\1', text)  # Remove italic
        text = re.sub(r'~~([^~]+)~~', r'\1', text)  # Remove strikethrough
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)  # Remove headers
        text = re.sub(r'&gt;.*$', '', text, flags=re.MULTILINE)  # Remove quotes
        text = re.sub(r'/u/\w+', '', text)  # Remove user mentions
        text = re.sub(r'/r/\w+', '', text)  # Remove subreddit mentions
        text = re.sub(r'https?://\S+', '', text)  # Remove URLs
        
        # Clean whitespace
        text = re.sub(r'\n+', ' ', text)  # Replace newlines with spaces
        text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces
        text = text.strip()
        
        return text

    def scrape_cricket_content(self, num_posts=200, include_comments=True, sort_methods=["hot", "top"]):
        """Comprehensive cricket content scraping"""
        all_content = []
        
        logger.info(f"🏏 Starting Reddit r/cricket scraping...")
        logger.info(f"📊 Target: {num_posts} posts per sort method")
        logger.info(f"🗨️  Include comments: {include_comments}")
        
        for sort_method in sort_methods:
            logger.info(f"📥 Scraping {sort_method} posts...")
            
            # Scrape posts
            posts = self.scrape_subreddit_posts(
                subreddit="cricket", 
                limit=min(num_posts, 100),  # Reddit API limit
                sort=sort_method
            )
            
            if not posts:
                logger.warning(f"No posts found for {sort_method} sort")
                continue
            
            all_content.extend(posts)
            logger.info(f"✅ Found {len(posts)} posts from {sort_method}")
            
            # Scrape comments if requested
            if include_comments:
                logger.info(f"🗨️  Scraping comments for {sort_method} posts...")
                
                # Use threading for comment scraping
                comments_collected = 0
                post_ids = [post['id'] for post in posts[:50]]  # Limit to first 50 posts
                
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    future_to_post = {executor.submit(self.scrape_post_comments, post_id): post_id 
                                    for post_id in post_ids}
                    
                    for future in as_completed(future_to_post):
                        post_id = future_to_post[future]
                        
                        try:
                            comments = future.result()
                            if comments:
                                all_content.extend(comments)
                                comments_collected += len(comments)
                                
                        except Exception as e:
                            logger.error(f"Error scraping comments for {post_id}: {e}")
                
                logger.info(f"✅ Collected {comments_collected} comments from {sort_method}")
        
        return all_content

    def save_content(self, content_data, filename_prefix):
        """Save scraped content to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save to JSON
        json_filename = f"{filename_prefix}_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(content_data, f, indent=2, ensure_ascii=False)
        
        # Save to CSV
        csv_filename = f"{filename_prefix}_{timestamp}.csv"
        if content_data:
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                fieldnames = content_data[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(content_data)
        
        logger.info(f"Content saved to {json_filename} and {csv_filename}")
        return json_filename, csv_filename

    def generate_summary(self, content_data):
        """Generate summary statistics"""
        if not content_data:
            return {}
        
        posts = [item for item in content_data if item.get('content_type') == 'post']
        comments = [item for item in content_data if item.get('content_type') == 'comment']
        
        total_words = sum(item.get('word_count', 0) for item in content_data)
        
        # Top flairs
        flairs = [post.get('flair_text', '') for post in posts if post.get('flair_text')]
        flair_counts = {}
        for flair in flairs:
            flair_counts[flair] = flair_counts.get(flair, 0) + 1
        
        return {
            'total_items': len(content_data),
            'posts': len(posts),
            'comments': len(comments),
            'total_words': total_words,
            'average_words_per_item': total_words / len(content_data) if content_data else 0,
            'top_flairs': dict(sorted(flair_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        }

def main():
    """Main function to scrape Reddit cricket content"""
    scraper = RedditCricketScraper()
    
    print("🏏 Reddit r/cricket Scraper")
    print("=" * 40)
    
    # Configuration
    num_posts = 100  # Posts per sort method
    include_comments = True
    sort_methods = ["hot", "top", "new"]
    
    print(f"📊 Configuration:")
    print(f"   Posts per sort method: {num_posts}")
    print(f"   Sort methods: {sort_methods}")
    print(f"   Include comments: {include_comments}")
    print(f"   Max workers: {scraper.max_workers}")
    
    # Ask user if they want to proceed
    response = input("\n🚀 Start scraping? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled by user")
        return
    
    start_time = time.time()
    
    # Scrape cricket content
    all_content = scraper.scrape_cricket_content(
        num_posts=num_posts,
        include_comments=include_comments,
        sort_methods=sort_methods
    )
    
    if all_content:
        # Save content
        json_file, csv_file = scraper.save_content(all_content, "reddit_cricket_content")
        
        # Generate summary
        summary = scraper.generate_summary(all_content)
        
        elapsed_time = time.time() - start_time
        
        print(f"\n🎉 Reddit scraping completed!")
        print(f"=" * 40)
        print(f"📊 Summary:")
        print(f"   Total items: {summary['total_items']}")
        print(f"   Posts: {summary['posts']}")
        print(f"   Comments: {summary['comments']}")
        print(f"   Total words: {summary['total_words']:,}")
        print(f"   Average words per item: {summary['average_words_per_item']:.1f}")
        print(f"   Time taken: {elapsed_time/60:.1f} minutes")
        
        print(f"\n🏷️  Top post flairs:")
        for flair, count in list(summary['top_flairs'].items())[:5]:
            print(f"   {flair}: {count} posts")
        
        print(f"\n💾 Files saved:")
        print(f"   📄 JSON: {json_file}")
        print(f"   📄 CSV: {csv_file}")
        
        print(f"\n🎯 Ready for cricket chatbot integration!")
        
    else:
        print("❌ No content was scraped")

if __name__ == "__main__":
    main()