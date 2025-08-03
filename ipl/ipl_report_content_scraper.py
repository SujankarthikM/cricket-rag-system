#!/usr/bin/env python3
"""
IPL Report Content Scraper
Visits each report link and extracts the full match report content
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse
import logging
from pathlib import Path
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IPLReportContentScraper:
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
        self.delay = 1  # Reduced delay for threading
        self._cookies_set = False
        self.scraped_count = 0
        self.failed_count = 0
        self.lock = Lock()  # Thread-safe counter updates
        self.max_workers = 10  # Number of concurrent threads
        
    def setup_session(self):
        """Initialize session with cookies"""
        if not self._cookies_set:
            try:
                logger.info("Getting cookies from main page...")
                main_response = self.session.get("https://www.espncricinfo.com/", timeout=10)
                self._cookies_set = True
                time.sleep(2)
                logger.info("Session initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize session: {e}")

    def get_page(self, url, retries=3):
        """Fetch a page with error handling"""
        for attempt in range(retries):
            try:
                headers = {
                    'Referer': 'https://www.espncricinfo.com/',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'same-origin',
                }
                
                response = self.session.get(url, timeout=15, headers=headers)
                
                if response.status_code == 200:
                    time.sleep(self.delay)
                    return response
                else:
                    logger.warning(f"Status code {response.status_code} for {url}")
                
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                
            if attempt == retries - 1:
                logger.error(f"Failed to fetch {url} after {retries} attempts")
                return None
            time.sleep(self.delay * (attempt + 1))
        return None

    def extract_report_content(self, soup, url):
        """Extract the match report content from the page - ONLY from p tags"""
        report_data = {
            'url': url,
            'title': '',
            'content': '',
            'summary': '',
            'teams': [],
            'date': '',
            'venue': '',
            'result': '',
            'word_count': 0,
            'scraped_at': datetime.now().isoformat()
        }
        
        try:
            # Extract title
            title_selectors = [
                'h1',
                '.match-header h1',
                '.article-title',
                '[data-testid="headline"]',
                '.headline'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    report_data['title'] = title_elem.get_text(strip=True)
                    break
            
            # ONLY extract text from <p> tags - no other elements
            paragraphs = soup.find_all('p')
            content_paragraphs = []
            
            for p in paragraphs:
                # Get clean text from paragraph
                p_text = p.get_text(strip=True)
                
                # Skip empty paragraphs and paragraphs with only special characters
                if p_text and len(p_text) > 10:  # Only paragraphs with substantial content
                    # Remove extra whitespace and clean up
                    clean_text = ' '.join(p_text.split())
                    content_paragraphs.append(clean_text)
            
            # Join paragraphs with double newlines for readability
            content_text = '\n\n'.join(content_paragraphs)
            
            report_data['content'] = content_text
            report_data['word_count'] = len(content_text.split()) if content_text else 0
            
            # Extract summary (first paragraph usually)
            if content_text:
                first_paragraph = content_text.split('\n')[0] if '\n' in content_text else content_text[:300]
                report_data['summary'] = first_paragraph[:300] + "..." if len(first_paragraph) > 300 else first_paragraph
            
            # Extract teams from title or URL
            teams = self.extract_teams_from_text(report_data['title'] + ' ' + url)
            report_data['teams'] = teams
            
            # Extract match details
            details = self.extract_match_details(soup)
            report_data.update(details)
            
        except Exception as e:
            logger.warning(f"Error extracting content from {url}: {e}")
        
        return report_data

    def extract_teams_from_text(self, text):
        """Extract team names from text"""
        # Common IPL team patterns
        teams_patterns = [
            r'mumbai\s+indians?|mi\b',
            r'chennai\s+super\s+kings?|csk\b',
            r'royal\s+challengers?\s+bangalore|rcb\b',
            r'kolkata\s+knight\s+riders?|kkr\b',
            r'rajasthan\s+royals?|rr\b',
            r'punjab\s+kings?|pbks\b|kings?\s+xi\s+punjab|kxip\b',
            r'delhi\s+capitals?|dc\b|delhi\s+daredevils?|dd\b',
            r'sunrisers?\s+hyderabad|srh\b',
            r'gujarat\s+titans?|gt\b',
            r'lucknow\s+super\s+giants?|lsg\b',
            r'deccan\s+chargers?',
            r'pune\s+warriors?',
            r'rising\s+pune\s+supergiant?|rps\b'
        ]
        
        found_teams = []
        text_lower = text.lower()
        
        for pattern in teams_patterns:
            if re.search(pattern, text_lower):
                # Extract the actual team name
                match = re.search(pattern, text_lower)
                if match:
                    team_name = match.group().title()
                    if team_name not in found_teams:
                        found_teams.append(team_name)
        
        return found_teams[:2]  # Return max 2 teams

    def extract_match_details(self, soup):
        """Extract additional match details like date, venue, result"""
        details = {
            'date': '',
            'venue': '',
            'result': ''
        }
        
        try:
            # Look for match details in various common locations
            detail_selectors = [
                '.match-details',
                '.match-info',
                '[data-testid="match-info"]',
                '.game-details'
            ]
            
            for selector in detail_selectors:
                details_section = soup.select_one(selector)
                if details_section:
                    details_text = details_section.get_text()
                    
                    # Extract date
                    date_match = re.search(r'\d{1,2}\s+\w+\s+\d{4}', details_text)
                    if date_match:
                        details['date'] = date_match.group()
                    
                    # Extract venue
                    venue_match = re.search(r'at\s+([^,\n]+)', details_text)
                    if venue_match:
                        details['venue'] = venue_match.group(1).strip()
                    
                    break
            
            # Extract result from content
            result_patterns = [
                r'won by \d+ runs?',
                r'won by \d+ wickets?',
                r'tied',
                r'no result',
                r'abandoned'
            ]
            
            page_text = soup.get_text().lower()
            for pattern in result_patterns:
                result_match = re.search(pattern, page_text)
                if result_match:
                    details['result'] = result_match.group()
                    break
                    
        except Exception as e:
            logger.warning(f"Error extracting match details: {e}")
        
        return details

    def load_report_links(self, filename):
        """Load the report links from the previous scraper"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                reports_data = json.load(f)
            logger.info(f"Loaded {len(reports_data)} report links from {filename}")
            return reports_data
        except FileNotFoundError:
            logger.error(f"Report links file not found: {filename}")
            return []
        except Exception as e:
            logger.error(f"Error loading report links: {e}")
            return []

    def scrape_report_content(self, report_link):
        """Scrape content from a single report URL - ONLY for indian-premier-league URLs"""
        url = report_link.get('url', '')
        if not url:
            return None
        
        # ONLY process URLs that contain "indian-premier-league"
        if 'ipl' not in url.lower():
            logger.debug(f"Skipping non-IPL URL: {url}")
            return None
        
        # Thread-safe counter update
        with self.lock:
            self.scraped_count += 1
            current_count = self.scraped_count
        
        # Log progress every 50 reports
        if current_count % 50 == 0:
            logger.info(f"Progress: {current_count} reports scraped")
        
        response = self.get_page(url)
        if not response:
            with self.lock:
                self.failed_count += 1
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        content_data = self.extract_report_content(soup, url)
        
        # Add original metadata
        content_data.update({
            'original_text': report_link.get('text', ''),
            'match_id': report_link.get('match_id', ''),
            'series_name': report_link.get('series_name', ''),
            'season': report_link.get('season', ''),
            'source_page': report_link.get('source_page', '')
        })
        
        return content_data

    def save_content(self, all_content, filename_prefix):
        """Save all report content to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save to JSON
        json_filename = f"{filename_prefix}_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(all_content, f, indent=2, ensure_ascii=False)
        
        # Save to CSV (with truncated content for readability)
        csv_filename = f"{filename_prefix}_{timestamp}.csv"
        if all_content:
            csv_data = []
            for item in all_content:
                csv_item = item.copy()
                # Truncate content for CSV
                if len(csv_item.get('content', '')) > 1000:
                    csv_item['content'] = csv_item['content'][:1000] + "..."
                csv_data.append(csv_item)
            
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                fieldnames = csv_data[0].keys() if csv_data else []
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
        
        logger.info(f"Content saved to {json_filename} and {csv_filename}")
        return json_filename, csv_filename

    def generate_content_summary(self, all_content):
        """Generate summary of scraped content"""
        if not all_content:
            return {}
        
        total_words = sum(item.get('word_count', 0) for item in all_content)
        successful_scrapes = len([item for item in all_content if item.get('content')])
        
        # Season distribution
        season_counts = {}
        for item in all_content:
            season = item.get('season', 'unknown')
            season_counts[season] = season_counts.get(season, 0) + 1
        
        # Average content length
        content_lengths = [item.get('word_count', 0) for item in all_content if item.get('word_count', 0) > 0]
        avg_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0
        
        return {
            'total_reports': len(all_content),
            'successful_scrapes': successful_scrapes,
            'failed_scrapes': len(all_content) - successful_scrapes,
            'total_words': total_words,
            'average_words_per_report': avg_length,
            'season_distribution': season_counts
        }

def main():
    """Main function to scrape all report content"""
    scraper = IPLReportContentScraper()
    
    print("🏏 IPL Match Report Content Scraper")
    print("=" * 60)
    
    # Setup session
    scraper.setup_session()
    
    # Find the most recent report links file
    report_files = list(Path('.').glob('ipl_all_match_reports_*.json'))
    if not report_files:
        print("❌ No IPL report links file found. Please run ipl_reports_scraper.py first.")
        return
    
    # Use the most recent file
    latest_file = max(report_files, key=lambda p: p.stat().st_mtime)
    print(f"📁 Using report links from: {latest_file}")
    
    # Load the report links
    report_links = scraper.load_report_links(latest_file)
    if not report_links:
        print("❌ Failed to load report links")
        return
    
    # Filter for only indian-premier-league URLs
    ipl_links = [link for link in report_links if 'ipl' in link.get('url', '').lower()]
    
    print(f"📊 Total report links loaded: {len(report_links)}")
    print(f"🏏 IPL-specific links (ipl): {len(ipl_links)}")
    print(f"🧵 Using {scraper.max_workers} concurrent threads")
    print(f"⏱️  Estimated time: {len(ipl_links) * 1 / scraper.max_workers / 60:.1f} minutes (with threading)")
    
    # Ask user if they want to proceed
    response = input("\n⚠️  This will take a while. Continue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled by user")
        return
    
    print(f"\n🚀 Starting content scraping with {scraper.max_workers} threads...")
    
    # Scrape content from each IPL report using threading
    all_content = []
    start_time = time.time()
    completed_count = 0
    
    # Use ThreadPoolExecutor for concurrent processing
    with ThreadPoolExecutor(max_workers=scraper.max_workers) as executor:
        try:
            # Submit all tasks
            future_to_link = {executor.submit(scraper.scrape_report_content, link): link 
                            for link in ipl_links}
            
            # Process completed tasks
            for future in as_completed(future_to_link):
                completed_count += 1
                
                # Update progress display
                progress_pct = (completed_count / len(ipl_links)) * 100
                print(f"\r📊 Progress: {completed_count}/{len(ipl_links)} ({progress_pct:.1f}%)", end='', flush=True)
                
                try:
                    content_data = future.result()
                    if content_data:
                        all_content.append(content_data)
                        
                except Exception as e:
                    link = future_to_link[future]
                    logger.error(f"Error processing report {link.get('url', '')}: {e}")
                
                # Save progress every 100 reports
                if completed_count % 100 == 0:
                    temp_filename = f"ipl_content_progress_{completed_count}"
                    scraper.save_content(all_content, temp_filename)
                    print(f"\n💾 Progress saved: {completed_count} reports completed")
                    
        except KeyboardInterrupt:
            print(f"\n⏹️  Interrupted by user. Saving progress...")
            executor.shutdown(wait=False)
    
    print(f"\n\n🎉 Content scraping completed!")
    
    # Save final results
    if all_content:
        json_file, csv_file = scraper.save_content(all_content, "ipl_complete_match_reports")
        
        # Generate and display summary
        summary = scraper.generate_content_summary(all_content)
        
        elapsed_time = time.time() - start_time
        
        print(f"=" * 60)
        print(f"📊 Final Summary:")
        print(f"   Total reports processed: {summary['total_reports']}")
        print(f"   Successful scrapes: {summary['successful_scrapes']}")
        print(f"   Failed scrapes: {summary['failed_scrapes']}")
        print(f"   Total words collected: {summary['total_words']:,}")
        print(f"   Average words per report: {summary['average_words_per_report']:.0f}")
        print(f"   Time taken: {elapsed_time/60:.1f} minutes")
        
        print(f"\n📈 Content by Season:")
        for season, count in sorted(summary['season_distribution'].items()):
            if count > 0:
                print(f"   {season}: {count} reports")
        
        print(f"\n💾 Files saved:")
        print(f"   📄 Complete JSON: {json_file}")
        print(f"   📄 Summary CSV: {csv_file}")
        
        print(f"\n🎯 Ready for RAG database import!")
    
    else:
        print("❌ No content was successfully scraped")

if __name__ == "__main__":
    main()