#!/usr/bin/env python3
"""
Reddit Cricket Discussion Scraper using PRAW
Collects substantial discussion content for RAG
"""

import praw
import json
import time
from datetime import datetime
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

class RedditCricketScraper:
    def __init__(self):
        # Initialize Reddit instance for read-only access
        # Using dummy credentials for read-only public access
        self.reddit = praw.Reddit(
            client_id="ragcricket",
            client_secret="toP-9J7dqyzjagsNPVb7xw", 
            user_agent="CricketBot/1.0 (Educational Research Project)"
        )
        
        self.subreddit = self.reddit.subreddit("cricket")
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
        
        # Require minimum 50 words
        if word_count < 50:
            return False
        
        # Avoid news/match threads
        avoid_keywords = [
            'breaking:', 'just in:', 'confirmed:', 'announced:', 'update:',
            'match thread', 'post match thread', 'live', 'scorecard',
            'highlights', 'squad announced', 'playing xi', 'injury update'
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
            'statistical analysis', 'technique', 'strategy'
        ]
        
        if any(indicator in text_lower for indicator in discussion_indicators):
            return True
        
        # Discussion flairs
        if flair:
            discussion_flairs = ['discussion', 'debate', 'opinion', 'analysis', 'question']
            if any(disc_flair in flair.lower() for disc_flair in discussion_flairs):
                return True
        
        # Long posts with questions
        if word_count > 100:
            question_patterns = ['what do you', 'how do you', 'why do you think', 'which is better']
            if any(pattern in text_lower for pattern in question_patterns):
                return True
        
        return False

    def is_quality_comment(self, comment_body, score):
        """Check if comment has quality discussion content"""
        
        word_count = len(comment_body.split())
        
        # Must be substantial (40+ words)
        if word_count < 40:
            return False
        
        # Avoid heavily downvoted
        if score < -3:
            return False
        
        text_lower = comment_body.lower()
        
        # Quality indicators
        quality_indicators = [
            'in my opinion', 'i believe', 'analysis', 'technique', 'strategy',
            'performance', 'comparison', 'statistical', 'tactical', 'technical',
            'career', 'playing style', 'approach', 'methodology', 'observation'
        ]
        
        if any(indicator in text_lower for indicator in quality_indicators):
            return True
        
        # Very long comments with basic discussion
        if word_count > 100:
            basic_indicators = ['i think', 'personally', 'my take', 'opinion']
            if any(indicator in text_lower for indicator in basic_indicators):
                return True
        
        return False

    def process_submission(self, submission):
        """Process a single submission and its comments"""
        try:
            # Check if it's substantial discussion
            if not self.is_substantial_discussion(
                submission.title, 
                submission.selftext, 
                submission.link_flair_text
            ):
                return []
            
            entries = []
            
            # Process the main post
            post_content = self.clean_text(f"{submission.title} {submission.selftext}")
            post_word_count = len(post_content.split())
            
            post_entry = {
                'type': 'discussion_post',
                'id': submission.id,
                'title': submission.title,
                'content': post_content,
                'word_count': post_word_count,
                'author': str(submission.author) if submission.author else '[deleted]',
                'score': submission.score,
                'num_comments': submission.num_comments,
                'flair': submission.link_flair_text,
                'created_utc': submission.created_utc,
                'created_date': datetime.fromtimestamp(submission.created_utc).isoformat(),
                'url': submission.url,
                'permalink': f"https://www.reddit.com{submission.permalink}",
                'source': 'reddit_praw_cricket_discussion',
                'content_category': 'opinion_discussion'
            }
            entries.append(post_entry)
            
            # Process comments
            submission.comments.replace_more(limit=0)  # Remove "more comments"
            comment_count = 0
            
            for comment in submission.comments.list():
                if hasattr(comment, 'body') and comment.body:
                    if self.is_quality_comment(comment.body, comment.score):
                        clean_comment = self.clean_text(comment.body)
                        comment_word_count = len(clean_comment.split())
                        
                        comment_entry = {
                            'type': 'discussion_comment',
                            'id': comment.id,
                            'post_id': submission.id,
                            'post_title': submission.title,
                            'content': clean_comment,
                            'word_count': comment_word_count,
                            'author': str(comment.author) if comment.author else '[deleted]',
                            'score': comment.score,
                            'created_utc': comment.created_utc,
                            'created_date': datetime.fromtimestamp(comment.created_utc).isoformat(),
                            'permalink': f"https://www.reddit.com{comment.permalink}",
                            'source': 'reddit_praw_cricket_comment',
                            'content_category': 'opinion_analysis'
                        }
                        entries.append(comment_entry)
                        comment_count += 1
                        
                        # Limit comments per post
                        if comment_count >= 20:
                            break
            
            print(f"✅ {submission.title[:50]}... | Post: {post_word_count}w | Comments: {comment_count}")
            return entries
            
        except Exception as e:
            print(f"❌ Error processing submission {submission.id}: {e}")
            return []

    def scrape_discussions(self, limit=1000):
        """Scrape substantial cricket discussions"""
        
        print("🏏 Reddit Cricket Discussion Scraper (PRAW)")
        print("🎯 Targeting substantial discussion content for RAG")
        print("=" * 60)
        
        all_data = []
        processed_count = 0
        
        # Get top posts from different time periods
        time_periods = ['all', 'year', 'month']
        
        for time_period in time_periods:
            print(f"\n📥 Fetching top posts from {time_period} time period...")
            
            try:
                if time_period == 'all':
                    submissions = list(self.subreddit.top(time_filter='all', limit=300))
                elif time_period == 'year':
                    submissions = list(self.subreddit.top(time_filter='year', limit=200))
                elif time_period == 'month':
                    submissions = list(self.subreddit.top(time_filter='month', limit=100))
                
                print(f"📊 Found {len(submissions)} posts from {time_period}")
                
                # Process submissions with threading
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = [executor.submit(self.process_submission, sub) for sub in submissions]
                    
                    for future in as_completed(futures):
                        try:
                            entries = future.result()
                            if entries:
                                all_data.extend(entries)
                                processed_count += 1
                                
                                # Break if we have enough data
                                if len(all_data) >= limit:
                                    print(f"🎯 Reached target of {limit} items!")
                                    break
                                    
                        except Exception as e:
                            print(f"❌ Thread error: {e}")
                    
                    if len(all_data) >= limit:
                        break
                        
            except Exception as e:
                print(f"❌ Error fetching {time_period} posts: {e}")
                continue
        
        return all_data

    def save_data(self, data):
        """Save scraped data to JSON"""
        if not data:
            print("❌ No data to save")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"reddit_praw_cricket_discussions_{timestamp}.json"
        
        # Calculate statistics
        posts = [item for item in data if item['type'] == 'discussion_post']
        comments = [item for item in data if item['type'] == 'discussion_comment']
        total_words = sum(item['word_count'] for item in data)
        
        dataset = {
            'metadata': {
                'source': 'reddit_r_cricket_praw',
                'content_type': 'substantial_discussions_and_analysis',
                'scraped_at': datetime.now().isoformat(),
                'total_items': len(data),
                'posts': len(posts),
                'comments': len(comments),
                'total_words': total_words,
                'average_words_per_item': total_words / len(data) if data else 0,
                'criteria': {
                    'min_post_words': 50,
                    'min_comment_words': 40,
                    'focus': 'discussions, debates, analysis, opinions',
                    'excluded': 'match threads, live updates, news announcements'
                }
            },
            'data': data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 Cricket Discussion Dataset Created!")
        print(f"📊 Total items: {len(data)}")
        print(f"📄 Discussion posts: {len(posts)}")
        print(f"💬 Quality comments: {len(comments)}")
        print(f"📝 Total words: {total_words:,}")
        print(f"📈 Average words per item: {total_words / len(data):.1f}")
        print(f"💾 Saved to: {filename}")
        
        return filename

def main():
    """Main function"""
    scraper = RedditCricketScraper()
    
    # Target substantial dataset
    target_items = 5000  # Aim for 5000 quality items
    
    print(f"🚀 Starting Reddit cricket discussion scraping...")
    print(f"🎯 Target: {target_items} quality discussion items")
    
    # Scrape discussions
    start_time = time.time()
    discussion_data = scraper.scrape_discussions(limit=target_items)
    
    if discussion_data:
        # Save the data
        filename = scraper.save_data(discussion_data)
        
        elapsed_time = time.time() - start_time
        print(f"⏱️  Time taken: {elapsed_time/60:.1f} minutes")
        print(f"🎯 Perfect for RAG: Rich cricket discussions and analysis!")
        
    else:
        print("❌ No substantial discussion content found")

if __name__ == "__main__":
    main()