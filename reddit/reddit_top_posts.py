#!/usr/bin/env python3
"""
Get top 5 posts of all time from r/cricket
"""

import requests
import json
from datetime import datetime, timezone
import time
import re

def clean_reddit_text(text):
    """Clean Reddit text for better RAG content"""
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

def get_post_comments(post_id, limit=100):
    """Get comments from a specific post for RAG data"""
    url = f"https://www.reddit.com/comments/{post_id}.json?limit={limit}&sort=top"
    
    headers = {
        'User-Agent': 'CricketBot/1.0 (Educational Research Project)',
        'Accept': 'application/json',
    }
    
    try:
        print(f"  📥 Fetching comments for post {post_id}...")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        comments_data = []
        
        if len(data) > 1 and 'data' in data[1]:
            comments = data[1]['data']['children']
            
            for comment in comments:
                if comment['kind'] == 't1':  # Comment type
                    comment_info = comment['data']
                    
                    # Clean and process comment text
                    body = comment_info.get('body', '')
                    clean_body = clean_reddit_text(body)
                    word_count = len(clean_body.split()) if clean_body else 0
                    
                    # Only include substantial comments (>20 words)
                    if word_count >= 20 and body != '[deleted]' and body != '[removed]':
                        comment_data = {
                            'id': comment_info.get('id'),
                            'author': comment_info.get('author', '[deleted]'),
                            'body': body,
                            'clean_body': clean_body,
                            'word_count': word_count,
                            'score': comment_info.get('score', 0),
                            'created_utc': comment_info.get('created_utc', 0),
                            'created_date': datetime.fromtimestamp(comment_info.get('created_utc', 0), tz=timezone.utc).isoformat(),
                            'permalink': f"https://www.reddit.com{comment_info.get('permalink', '')}",
                            'parent_id': comment_info.get('parent_id', ''),
                            'depth': comment_info.get('depth', 0)
                        }
                        comments_data.append(comment_data)
        
        # Sort by score and return top comments
        comments_data.sort(key=lambda x: x['score'], reverse=True)
        top_comments = comments_data[:50]  # Top 50 comments
        
        print(f"  ✅ Found {len(top_comments)} quality comments")
        return top_comments
        
    except Exception as e:
        print(f"  ❌ Error fetching comments: {e}")
        return []

def is_discussion_content(title, selftext, flair):
    """Check if post contains any meaningful content suitable for RAG (very lenient)"""
    
    # Basic text requirement - just need some content
    total_text = f"{title} {selftext}".strip()
    word_count = len(total_text.split())
    
    # Very lenient - just need more than title alone
    if word_count < 10:
        return False
    
    # Only exclude very specific unwanted content
    strict_avoid_keywords = [
        'match thread:', 'post match thread:', '[live]', 'scorecard'
    ]
    
    text_to_check = f"{title} {selftext} {flair}".lower()
    
    # Only reject very obvious live/match threads
    if any(keyword in text_to_check for keyword in strict_avoid_keywords):
        return False
    
    # Accept almost everything else:
    
    # 1. Any post with selftext content
    if len(selftext.split()) > 5:
        return True
    
    # 2. Any post with discussion-related words
    broad_discussion_words = [
        'think', 'opinion', 'feel', 'believe', 'discuss', 'debate', 'question',
        'why', 'how', 'what', 'who', 'best', 'worst', 'better', 'good', 'bad',
        'analysis', 'review', 'comparison', 'vs', 'versus', 'against',
        'should', 'would', 'could', 'will', 'might', 'maybe', 'perhaps',
        'agree', 'disagree', 'right', 'wrong', 'correct', 'mistake',
        'favorite', 'favourite', 'like', 'love', 'hate', 'prefer',
        'ranking', 'rank', 'rate', 'rating', 'score', 'grade'
    ]
    
    if any(word in text_to_check for word in broad_discussion_words):
        return True
    
    # 3. Any post with cricket-related content and questions
    cricket_terms = [
        'cricket', 'bat', 'ball', 'bowl', 'field', 'wicket', 'run', 'over',
        'team', 'player', 'captain', 'match', 'game', 'series', 'tournament',
        'ipl', 'test', 'odi', 't20', 'world cup', 'india', 'australia', 'england'
    ]
    
    question_indicators = ['?', 'why', 'how', 'what', 'who', 'when', 'where', 'which']
    
    has_cricket = any(term in text_to_check for term in cricket_terms)
    has_question = any(indicator in text_to_check for indicator in question_indicators)
    
    if has_cricket and (has_question or word_count > 15):
        return True
    
    # 4. Accept any longer posts (likely to have content)
    if word_count > 25:
        return True
    
    return False

def is_quality_comment(comment_text, score):
    """Check if comment contains any meaningful content for RAG (very lenient)"""
    
    # Much more lenient - just need some substance
    word_count = len(comment_text.split())
    if word_count < 15:  # Much lower threshold
        return False
    
    # Only exclude heavily downvoted
    if score < -5:
        return False
    
    text_lower = comment_text.lower()
    
    # Accept almost all comments with basic discussion indicators
    basic_discussion_words = [
        'i think', 'i believe', 'opinion', 'feel', 'agree', 'disagree',
        'good', 'bad', 'better', 'worse', 'best', 'worst', 'like', 'love',
        'analysis', 'review', 'comparison', 'vs', 'against', 'technique',
        'strategy', 'performance', 'skill', 'talent', 'ability', 'player',
        'team', 'captain', 'match', 'game', 'series', 'tournament',
        'batting', 'bowling', 'fielding', 'wicket', 'run', 'over',
        'why', 'how', 'what', 'because', 'since', 'however', 'but',
        'should', 'would', 'could', 'might', 'maybe', 'probably'
    ]
    
    # Accept if has any discussion words
    if any(word in text_lower for word in basic_discussion_words):
        return True
    
    # Accept longer comments (likely to have substance)
    if word_count > 30:
        return True
    
    # Accept comments with cricket content
    cricket_terms = [
        'cricket', 'bat', 'ball', 'bowl', 'field', 'wicket', 'run', 'over',
        'team', 'player', 'captain', 'match', 'game', 'ipl', 'test', 'odi'
    ]
    
    if any(term in text_lower for term in cricket_terms) and word_count > 20:
        return True
    
    return False

def get_discussion_cricket_posts(limit=50, sort_methods=['hot', 'top'], time_periods=['all', 'year', 'month', 'week']):
    """Get discussion-focused cricket posts suitable for RAG"""
    
    print("🏏 Getting Discussion-Focused Cricket Posts for RAG")
    print("=" * 60)
    
    all_rag_data = []
    total_words = 0
    
    headers = {
        'User-Agent': 'CricketBot/1.0 (Educational Research Project)',
        'Accept': 'application/json',
    }
    
    # Threading for parallel processing
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from threading import Lock
    
    discussion_posts_lock = Lock()
    
    def fetch_posts_for_period(sort_method, time_period):
        """Fetch posts for a specific time period with pagination for 'all' time"""
        period_posts = []
        
        # For 'all' time period, fetch multiple pages to get more data
        if time_period == 'all':
            pages_to_fetch = 10000  # Fetch 50 pages for 'all' time (5000 posts total)
            after_token = None
            
            for page in range(pages_to_fetch):
                # Build URL with pagination
                if sort_method == 'top':
                    if after_token:
                        url = f"https://www.reddit.com/r/cricket/{sort_method}.json?limit=100&t={time_period}&after={after_token}"
                    else:
                        url = f"https://www.reddit.com/r/cricket/{sort_method}.json?limit=100&t={time_period}"
                else:
                    if after_token:
                        url = f"https://www.reddit.com/r/cricket/{sort_method}.json?limit=100&after={after_token}"
                    else:
                        url = f"https://www.reddit.com/r/cricket/{sort_method}.json?limit=100"
                
                print(f"📥 Fetching {sort_method} posts for {time_period} period (page {page+1})...")
                
                try:
                    response = requests.get(url, headers=headers, timeout=30)
                    response.raise_for_status()
                    
                    data = response.json()
                    posts = data['data']['children']
                    after_token = data['data'].get('after')
                    
                    page_discussion_posts = 0
                    for post in posts:
                        post_data = post['data']
                        title = post_data.get('title', '')
                        selftext = post_data.get('selftext', '')
                        flair = post_data.get('link_flair_text', '')
                        score = post_data.get('score', 0)
                        num_comments = post_data.get('num_comments', 0)
                        
                        # Include all discussion posts (very lenient)
                        if is_discussion_content(title, selftext, flair):
                            period_posts.append((post, sort_method, time_period))
                            page_discussion_posts += 1
                    
                    print(f"✅ Page {page+1}: Found {page_discussion_posts} discussion posts")
                    
                    # Break if no more pages or no posts found
                    if not after_token or len(posts) == 0:
                        print(f"📝 No more pages available after page {page+1}")
                        break
                    
                    time.sleep(2.0)  # Longer delay between pages to avoid rate limiting
                    
                except Exception as e:
                    if "429" in str(e):  # Rate limited
                        print(f"⏳ Rate limited on page {page+1}, waiting 15 seconds...")
                        time.sleep(15)
                        continue
                    elif "timeout" in str(e).lower():  # Timeout
                        print(f"⏳ Timeout on page {page+1}, retrying in 5 seconds...")
                        time.sleep(5)
                        continue
                    else:
                        print(f"❌ Error fetching page {page+1} for {sort_method}-{time_period}: {e}")
                        break
        
        else:
            # Regular single-page fetch for other time periods
            if sort_method == 'top' and time_period != 'hot':
                url = f"https://www.reddit.com/r/cricket/{sort_method}.json?limit={limit}&t={time_period}"
            else:
                url = f"https://www.reddit.com/r/cricket/{sort_method}.json?limit={limit}"
            
            print(f"📥 Fetching {sort_method} posts for {time_period} period...")
            
            try:
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                posts = data['data']['children']
                
                for post in posts:
                    post_data = post['data']
                    title = post_data.get('title', '')
                    selftext = post_data.get('selftext', '')
                    flair = post_data.get('link_flair_text', '')
                    score = post_data.get('score', 0)
                    num_comments = post_data.get('num_comments', 0)
                    
                    # Include all discussion posts (very lenient)
                    if is_discussion_content(title, selftext, flair):
                        period_posts.append((post, sort_method, time_period))
                
            except Exception as e:
                print(f"❌ Error fetching {sort_method}-{time_period} posts: {e}")
        
        print(f"🎯 Total discussion posts from {sort_method}-{time_period}: {len(period_posts)}")
        return period_posts
    
    # Collect all posts with threading
    all_posts_to_process = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:  # Reduce workers to avoid rate limiting
        # Create futures for different sort/time combinations
        futures = []
        
        for sort_method in sort_methods:
            if sort_method == 'top':
                # For 'top', fetch from different time periods
                for time_period in time_periods:
                    futures.append(executor.submit(fetch_posts_for_period, sort_method, time_period))
            else:
                # For 'hot', 'new', etc., just fetch once
                futures.append(executor.submit(fetch_posts_for_period, sort_method, 'current'))
        
        # Collect results
        for future in as_completed(futures):
            try:
                period_posts = future.result()
                all_posts_to_process.extend(period_posts)
            except Exception as e:
                print(f"❌ Thread error: {e}")
    
    # Remove duplicates based on post ID
    unique_posts = {}
    for post_tuple in all_posts_to_process:
        post, sort_method, time_period = post_tuple
        post_id = post['data'].get('id')
        if post_id not in unique_posts:
            unique_posts[post_id] = post_tuple
    
    print(f"\n🎯 Total unique discussion posts found: {len(unique_posts)}")
    
    # Process posts with threading
    def process_single_post(post_tuple):
        """Process a single post and its comments"""
        post, sort_method, time_period = post_tuple
        post_data = post['data']
        
        post_id = post_data.get('id')
        title = post_data.get('title', '')
        selftext = post_data.get('selftext', '')
        author = post_data.get('author', '[deleted]')
        score = post_data.get('score', 0)
        num_comments = post_data.get('num_comments', 0)
        flair = post_data.get('link_flair_text', '')
        created_utc = post_data.get('created_utc', 0)
        created_date = datetime.fromtimestamp(created_utc, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        permalink = f"https://www.reddit.com{post_data.get('permalink', '')}"
        
        # Clean post content
        post_content = clean_reddit_text(f"{title} {selftext}")
        post_word_count = len(post_content.split()) if post_content else 0
        
        # Create post entry for RAG
        post_entry = {
            'type': 'discussion_post',
            'post_id': post_id,
            'title': title,
            'content': post_content,
            'raw_selftext': selftext,
            'word_count': post_word_count,
            'author': author,
            'score': score,
            'num_comments': num_comments,
            'flair': flair,
            'created_date': created_date,
            'permalink': permalink,
            'sort_method': sort_method,
            'time_period': time_period,
            'source': 'reddit_r_cricket_discussion',
            'content_category': 'opinion_discussion'
        }
        
        # Get quality comments
        time.sleep(1.5)  # Longer delay to avoid rate limiting
        comments = get_discussion_comments(post_id)
        
        post_entries = [post_entry]
        comment_words = 0
        quality_comments = 0
        
        for comment in comments:
            if is_quality_comment(comment['clean_body'], comment['score']):
                comment_entry = {
                    'type': 'discussion_comment',
                    'post_id': post_id,
                    'post_title': title,
                    'comment_id': comment['id'],
                    'content': comment['clean_body'],
                    'raw_body': comment['body'],
                    'word_count': comment['word_count'],
                    'author': comment['author'],
                    'score': comment['score'],
                    'created_date': comment['created_date'],
                    'permalink': comment['permalink'],
                    'sort_method': sort_method,
                    'time_period': time_period,
                    'source': 'reddit_r_cricket_discussion_comment',
                    'content_category': 'opinion_analysis'
                }
                post_entries.append(comment_entry)
                comment_words += comment['word_count']
                quality_comments += 1
        
        print(f"✅ {title[:40]}... | Post: {post_word_count}w | Comments: {quality_comments} ({comment_words}w)")
        return post_entries, post_word_count + comment_words
    
    # Process all posts with threading
    print(f"\n🔄 Processing posts and comments with threading...")
    
    with ThreadPoolExecutor(max_workers=8) as executor:  # Reduce workers to avoid rate limiting
        futures = [executor.submit(process_single_post, post_tuple) 
                  for post_tuple in list(unique_posts.values())[:2000]]  # Process 2000 posts for 8000+ total items
        
        for future in as_completed(futures):
            try:
                post_entries, word_count = future.result()
                all_rag_data.extend(post_entries)
                total_words += word_count
            except Exception as e:
                print(f"❌ Error processing post: {e}")
    
    return all_rag_data, total_words

def get_discussion_comments(post_id, limit=100):
    """Get high-quality discussion comments"""
    url = f"https://www.reddit.com/comments/{post_id}.json?limit={limit}&sort=top"
    
    headers = {
        'User-Agent': 'CricketBot/1.0 (Educational Research Project)',
        'Accept': 'application/json',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        comments_data = []
        
        if len(data) > 1 and 'data' in data[1]:
            comments = data[1]['data']['children']
            
            for comment in comments:
                if comment['kind'] == 't1':
                    comment_info = comment['data']
                    
                    body = comment_info.get('body', '')
                    clean_body = clean_reddit_text(body)
                    word_count = len(clean_body.split()) if clean_body else 0
                    score = comment_info.get('score', 0)
                    
                    # Only substantial, quality comments
                    if (word_count >= 20 and body != '[deleted]' and 
                        body != '[removed]' and score >= 0):
                        
                        comment_data = {
                            'id': comment_info.get('id'),
                            'author': comment_info.get('author', '[deleted]'),
                            'body': body,
                            'clean_body': clean_body,
                            'word_count': word_count,
                            'score': score,
                            'created_utc': comment_info.get('created_utc', 0),
                            'created_date': datetime.fromtimestamp(comment_info.get('created_utc', 0), tz=timezone.utc).isoformat(),
                            'permalink': f"https://www.reddit.com{comment_info.get('permalink', '')}",
                            'parent_id': comment_info.get('parent_id', ''),
                            'depth': comment_info.get('depth', 0)
                        }
                        comments_data.append(comment_data)
        
        # Sort by score and return top comments
        comments_data.sort(key=lambda x: x['score'], reverse=True)
        return comments_data[:30]  # Top 30 quality comments
        
    except Exception as e:
        return []

def main_discussion_scraper():
    """Main function to get discussion-focused cricket content for RAG"""
    
    print("🎯 Smart Cricket Discussion Scraper for RAG")
    print("🔍 Filtering for: Opinions, Debates, Analysis, Discussions")
    print("❌ Avoiding: Match threads, Live scores, News updates")
    print("=" * 60)
    
    # Get discussion-focused content across different time periods
    # Focus heavily on 'all' time period for maximum historical data
    all_rag_data, total_words = get_discussion_cricket_posts(
        limit=100, 
        sort_methods=['top', 'hot', 'new'],  # Multiple sort methods for more variety
        time_periods=['all', 'year', 'month', 'week', 'day']  # More time periods for maximum data
    )
    
    if all_rag_data:
        # Save comprehensive RAG dataset
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"cricket_discussion_rag_data_{timestamp}.json"
        
        rag_dataset = {
            'metadata': {
                'source': 'reddit_r_cricket_discussions',
                'content_type': 'opinions_debates_analysis',
                'scraped_at': datetime.now().isoformat(),
                'total_items': len(all_rag_data),
                'total_words': total_words,
                'posts': len([item for item in all_rag_data if item['type'] == 'discussion_post']),
                'comments': len([item for item in all_rag_data if item['type'] == 'discussion_comment']),
                'filtering_criteria': {
                    'included': 'discussions, debates, opinions, analysis, comparisons',
                    'excluded': 'live threads, scores, breaking news, injury updates',
                    'min_comment_words': 20,
                    'min_post_score': 10,
                    'min_post_comments': 5
                }
            },
            'data': all_rag_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(rag_dataset, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 Smart Discussion RAG Dataset Created!")
        print(f"📊 Total items: {len(all_rag_data)}")
        print(f"📄 Discussion posts: {rag_dataset['metadata']['posts']}")
        print(f"💬 Quality comments: {rag_dataset['metadata']['comments']}")
        print(f"📝 Total words: {total_words:,}")
        print(f"💾 Saved to: {filename}")
        
        # Show content categories
        categories = {}
        for item in all_rag_data:
            cat = item.get('content_category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"\n📈 Content Categories:")
        for category, count in categories.items():
            print(f"   {category}: {count} items")
        
        print(f"\n🎯 Perfect for RAG: Rich discussions, opinions, and analysis!")
        
        return rag_dataset
        
    else:
        print("❌ No discussion content found")
        return None

if __name__ == "__main__":
    main_discussion_scraper()