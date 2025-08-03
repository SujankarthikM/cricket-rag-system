#!/usr/bin/env python3
"""
Test script for Reddit cricket scraper - tests on small dataset
"""

from reddit_cricket_scraper import RedditCricketScraper
import time

def test_reddit_scraper():
    """Test the Reddit scraper on small dataset"""
    print("🧪 Testing Reddit Cricket Scraper")
    print("=" * 40)
    
    scraper = RedditCricketScraper()
    
    print("📥 Testing subreddit posts scraping...")
    
    # Test basic post scraping (limit to 10 posts)
    posts = scraper.scrape_subreddit_posts(subreddit="cricket", limit=10, sort="hot")
    
    if posts:
        print(f"✅ Successfully scraped {len(posts)} posts")
        
        # Show sample posts
        print(f"\n📝 Sample posts:")
        for i, post in enumerate(posts[:3], 1):
            print(f"   {i}. {post['title'][:60]}...")
            print(f"      Score: {post['score']}, Comments: {post['num_comments']}")
            print(f"      Flair: {post.get('flair_text', 'No flair')}")
            print(f"      Words: {post['word_count']}")
        
        # Test comment scraping on first post
        if posts[0]['num_comments'] > 0:
            print(f"\n🗨️  Testing comment scraping on first post...")
            
            comments = scraper.scrape_post_comments(posts[0]['id'], limit=5)
            
            if comments:
                print(f"✅ Successfully scraped {len(comments)} comments")
                
                print(f"\n💬 Sample comments:")
                for i, comment in enumerate(comments[:2], 1):
                    print(f"   {i}. {comment['clean_text'][:80]}...")
                    print(f"      Score: {comment['score']}, Words: {comment['word_count']}")
            else:
                print("❌ No comments found")
        
        print(f"\n✅ Reddit scraper test completed successfully!")
        print(f"🎯 Ready for full scraping!")
        
    else:
        print("❌ Failed to scrape posts")

if __name__ == "__main__":
    test_reddit_scraper()