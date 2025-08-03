#!/usr/bin/env python3
"""
Enhanced Reddit Cricket Discussion Scraper
Collects substantial discussion content for RAG using requests (no auth needed)
"""

import requests
import json
import time
from datetime import datetime
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

class RedditCricketScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CricketBot/1.0 (Educational Research Project)',
            'Accept': 'application/json',
        })
        self.base_url = "https://www.reddit.com/r/cricket"
        self.scraped_data = []
        self.lock = Lock()
        
    def clean_text(self, text):
        """Clean Reddit text for RAG"""
        if not text:
            return ""
        
        # Remove Reddit markup
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Links
        text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*([^\*]+)\*', r'\1', text)  # Italic
        text = re.sub(r'~~([^~]+)~~', r'\1', text)  # Strikethrough
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)  # Headers
        text = re.sub(r'&gt;.*$', '', text, flags=re.MULTILINE)  # Quotes
        text = re.sub(r'/u/\w+', '', text)  # User mentions
        text = re.sub(r'/r/\w+', '', text)  # Subreddit mentions
        text = re.sub(r'https?://\S+', '', text)  # URLs
        
        # Clean whitespace
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text

    def is_substantial_discussion(self, title, selftext, flair):
        """Check if post has substantial discussion content for RAG"""
        
        # Must have meaningful content (not just title)
        total_text = f"{title} {selftext}".strip()
        word_count = len(total_text.split())
        
        # Require minimum 50 words for substantial content
        if word_count < 50:
            return False
        
        # Avoid news/match threads/announcements
        avoid_keywords = [
            'breaking:', 'just in:', 'confirmed:', 'announced:', 'update:',
            'match thread', 'post match thread', 'live', 'scorecard',
            'highlights', 'squad announced', 'playing xi', 'injury update',
            'toss', 'rain', 'weather', 'stumps', 'lunch', 'tea'
        ]
        
        text_lower = total_text.lower()
        if any(keyword in text_lower for keyword in avoid_keywords):
            return False
        
        # Strong discussion indicators
        discussion_indicators = [
            'what do you think', 'opinion', 'debate', 'discuss', 'analysis',
            'breakdown', 'review', 'comparison', 'unpopular opinion', 'hot take',
            'why i think', 'personally', 'controversial', 'change my mind',
            'career analysis', 'performance review', 'tactical analysis',
            'statistical analysis', 'technique breakdown', 'strategy discussion',
            'detailed look', 'comprehensive review', 'in-depth analysis',
            'historical perspective', 'long term view', 'retrospective'
        ]
        
        if any(indicator in text_lower for indicator in discussion_indicators):
            return True
        
        # Discussion flairs with substantial content
        if flair:
            discussion_flairs = ['discussion', 'debate', 'opinion', 'analysis', 'question']
            if any(disc_flair in flair.lower() for disc_flair in discussion_flairs):
                if word_count > 80:  # Higher threshold for flair posts
                    return True
        
        # Long analytical posts
        if word_count > 150:
            analytical_patterns = [
                'analysis of', 'breakdown of', 'review of', 'comparison between',
                'statistical look', 'tactical review', 'performance analysis',
                'playing style', 'technique analysis', 'strategy discussion'
            ]
            if any(pattern in text_lower for pattern in analytical_patterns):
                return True
        
        return False

    def is_quality_comment(self, comment_body, score):
        """Check if comment has quality discussion content"""
        
        word_count = len(comment_body.split())
        
        # Must be substantial (50+ words for high quality)
        if word_count < 50:
            return False
        
        # Avoid heavily downvoted
        if score < -2:
            return False
        
        text_lower = comment_body.lower()
        
        # High-quality discussion indicators
        quality_indicators = [
            'in my opinion', 'i believe that', 'analysis shows', 'statistically',
            'technique', 'strategy', 'tactical', 'performance analysis',
            'comparison with', 'historical context', 'career trajectory',
            'playing style', 'approach', 'methodology', 'observation',
            'based on', 'evidence suggests', 'data shows', 'research indicates'
        ]
        
        if any(indicator in text_lower for indicator in quality_indicators):
            return True
        
        # Very long analytical comments
        if word_count > 100:
            analytical_indicators = [
                'breakdown', 'analysis', 'detailed', 'comprehensive',
                'perspective', 'observation', 'comparison', 'evaluation'
            ]
            if any(indicator in text_lower for indicator in analytical_indicators):
                return True
        
        return False

    def fetch_posts(self, sort_type, time_filter=None, limit=100):
        """Fetch posts from Reddit"""
        if time_filter:
            url = f"{self.base_url}/{sort_type}.json?limit={limit}&t={time_filter}"
        else:
            url = f"{self.base_url}/{sort_type}.json?limit={limit}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error fetching {sort_type} posts: {e}")
            return None

    def fetch_comments(self, post_id, limit=200):
        """Fetch comments for a post"""
        url = f"https://www.reddit.com/comments/{post_id}.json?limit={limit}&sort=top"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error fetching comments for {post_id}: {e}")
            return None

    def process_post(self, post_data):
        """Process a single post and its comments"""
        try:
            title = post_data.get('title', '')
            selftext = post_data.get('selftext', '')
            flair = post_data.get('link_flair_text', '')
            
            # Check if it's substantial discussion
            if not self.is_substantial_discussion(title, selftext, flair):
                return []
            
            entries = []
            
            # Process the main post
            post_content = self.clean_text(f"{title} {selftext}")
            post_word_count = len(post_content.split())
            
            # Skip if cleaned content is too short
            if post_word_count < 30:
                return []
            
            post_entry = {
                'type': 'discussion_post',
                'id': post_data.get('id'),
                'title': title,
                'content': post_content,
                'word_count': post_word_count,
                'author': post_data.get('author', '[deleted]'),
                'score': post_data.get('score', 0),
                'num_comments': post_data.get('num_comments', 0),
                'flair': flair,
                'created_utc': post_data.get('created_utc', 0),
                'created_date': datetime.fromtimestamp(post_data.get('created_utc', 0)).isoformat(),
                'permalink': f"https://www.reddit.com{post_data.get('permalink', '')}",
                'source': 'reddit_enhanced_cricket_discussion',
                'content_category': 'substantial_discussion'
            }
            entries.append(post_entry)
            
            # Process comments
            post_id = post_data.get('id')
            comments_data = self.fetch_comments(post_id)
            
            if comments_data and len(comments_data) > 1:
                comment_count = 0
                comments_list = comments_data[1]['data']['children']
                
                for comment in comments_list:
                    if comment['kind'] == 't1':
                        comment_info = comment['data']
                        body = comment_info.get('body', '')
                        score = comment_info.get('score', 0)
                        
                        if body and body not in ['[deleted]', '[removed]']:
                            if self.is_quality_comment(body, score):
                                clean_comment = self.clean_text(body)
                                comment_word_count = len(clean_comment.split())
                                
                                if comment_word_count >= 30:  # Final check for substantial content
                                    comment_entry = {
                                        'type': 'discussion_comment',
                                        'id': comment_info.get('id'),
                                        'post_id': post_id,
                                        'post_title': title,
                                        'content': clean_comment,
                                        'word_count': comment_word_count,
                                        'author': comment_info.get('author', '[deleted]'),
                                        'score': score,
                                        'created_utc': comment_info.get('created_utc', 0),
                                        'created_date': datetime.fromtimestamp(comment_info.get('created_utc', 0)).isoformat(),
                                        'permalink': f"https://www.reddit.com{comment_info.get('permalink', '')}",
                                        'source': 'reddit_enhanced_cricket_comment',
                                        'content_category': 'analytical_discussion'
                                    }
                                    entries.append(comment_entry)
                                    comment_count += 1
                                    
                                    # Limit comments per post
                                    if comment_count >= 15:
                                        break
            
            if len(entries) > 1:  # Only return if we have post + at least some comments
                print(f"✅ {title[:40]}... | Post: {post_word_count}w | Comments: {len(entries)-1}")
            
            time.sleep(0.5)  # Rate limiting
            return entries
            
        except Exception as e:
            print(f"❌ Error processing post: {e}")
            return []

    def scrape_substantial_discussions(self, target_items=5000):
        """Scrape substantial cricket discussions"""
        
        print("🏏 Enhanced Reddit Cricket Discussion Scraper")
        print("🎯 Targeting substantial discussion content for RAG")
        print("📊 Minimum requirements: 50+ words per post, 50+ words per comment")
        print("=" * 70)
        
        all_data = []
        
        # Configuration for different sources
        sources = [
            ('top', 'all', 200),      # Top all-time posts
            ('top', 'year', 150),     # Top yearly posts  
            ('top', 'month', 100),    # Top monthly posts
            ('hot', None, 100),       # Current hot posts
        ]
        
        for sort_type, time_filter, limit in sources:
            time_desc = f"{sort_type}-{time_filter}" if time_filter else sort_type
            print(f"\n📥 Fetching {time_desc} posts (limit: {limit})...")
            
            # Fetch posts
            data = self.fetch_posts(sort_type, time_filter, limit)
            if not data or 'data' not in data or 'children' not in data['data']:
                print(f"❌ No data found for {time_desc}")
                continue
            
            posts = data['data']['children']
            print(f"📊 Found {len(posts)} posts from {time_desc}")
            
            # Process posts with threading
            processed_count = 0
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(self.process_post, post['data']) for post in posts]
                
                for future in as_completed(futures):
                    try:
                        entries = future.result()
                        if entries:
                            all_data.extend(entries)
                            processed_count += 1
                            
                            # Check if we've reached target
                            if len(all_data) >= target_items:
                                print(f"🎯 Reached target of {target_items} items!")
                                break
                                
                    except Exception as e:
                        print(f"❌ Thread error: {e}")
                
                if len(all_data) >= target_items:
                    break
            
            print(f"✅ Processed {processed_count} posts from {time_desc}")
            print(f"📈 Total items collected so far: {len(all_data)}")
            
            # Small delay between different sources
            time.sleep(2)
        
        return all_data

    def save_dataset(self, data):
        """Save the dataset with comprehensive metadata"""
        if not data:
            print("❌ No data to save")
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"cricket_enhanced_discussions_{timestamp}.json"
        
        # Calculate detailed statistics
        posts = [item for item in data if item['type'] == 'discussion_post']
        comments = [item for item in data if item['type'] == 'discussion_comment']
        total_words = sum(item['word_count'] for item in data)
        
        post_words = sum(item['word_count'] for item in posts)
        comment_words = sum(item['word_count'] for item in comments)
        
        dataset = {
            'metadata': {
                'source': 'reddit_r_cricket_enhanced',
                'content_type': 'substantial_cricket_discussions_and_analysis',
                'scraping_method': 'enhanced_filtering_for_quality',
                'scraped_at': datetime.now().isoformat(),
                'total_items': len(data),
                'breakdown': {
                    'discussion_posts': len(posts),
                    'analytical_comments': len(comments)
                },
                'word_statistics': {
                    'total_words': total_words,
                    'post_words': post_words,
                    'comment_words': comment_words,
                    'average_words_per_item': round(total_words / len(data), 1) if data else 0,
                    'average_words_per_post': round(post_words / len(posts), 1) if posts else 0,
                    'average_words_per_comment': round(comment_words / len(comments), 1) if comments else 0
                },
                'quality_criteria': {
                    'minimum_post_words': 50,
                    'minimum_comment_words': 50,
                    'content_focus': 'discussions, debates, analysis, opinions, technical breakdowns',
                    'excluded_content': 'match threads, live updates, news announcements, short reactions',
                    'filtering_approach': 'keyword-based + word count + engagement metrics'
                }
            },
            'data': data
        }
        
        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        # Display comprehensive results
        print(f"\n🎉 Enhanced Cricket Discussion Dataset Created!")
        print(f"=" * 50)
        print(f"📊 Dataset Statistics:")
        print(f"   Total items: {len(data):,}")
        print(f"   Discussion posts: {len(posts):,}")
        print(f"   Analytical comments: {len(comments):,}")
        print(f"")
        print(f"📝 Content Statistics:")
        print(f"   Total words: {total_words:,}")
        print(f"   Post words: {post_words:,}")
        print(f"   Comment words: {comment_words:,}")
        print(f"   Average words per item: {dataset['metadata']['word_statistics']['average_words_per_item']}")
        print(f"")
        print(f"💾 File: {filename}")
        print(f"🎯 Perfect for RAG: High-quality cricket discussions and analysis!")
        
        return filename

def main():
    """Main execution function"""
    scraper = RedditCricketScraper()
    
    # Target for substantial dataset
    target_items = 8000  # Aim for 8000 quality items
    
    print(f"🚀 Starting enhanced Reddit cricket discussion scraping...")
    print(f"🎯 Target: {target_items:,} high-quality discussion items")
    print(f"⚡ Using threading for faster processing")
    
    # Start scraping
    start_time = time.time()
    discussion_data = scraper.scrape_substantial_discussions(target_items)
    
    if discussion_data:
        # Save the comprehensive dataset
        filename = scraper.save_dataset(discussion_data)
        
        elapsed_time = time.time() - start_time
        print(f"\n⏱️  Scraping completed in: {elapsed_time/60:.1f} minutes")
        print(f"📈 Items per minute: {len(discussion_data)/(elapsed_time/60):.1f}")
        
    else:
        print("❌ No substantial discussion content found")

if __name__ == "__main__":
    main()