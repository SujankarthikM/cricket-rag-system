#!/usr/bin/env python3
"""
IPL Match Reports Scraper
Scrapes all match report links from each of the 18 IPL series
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import time
from datetime import datetime
from urllib.parse import urljoin
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IPLReportsScraper:
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
        self.delay = 3  # Respectful delay between requests
        self._cookies_set = False
        
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
                logger.info(f"Fetching: {url} (Attempt {attempt + 1})")
                
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
                    logger.warning(f"Status code: {response.status_code}")
                
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
            if attempt == retries - 1:
                logger.error(f"Failed to fetch {url} after {retries} attempts")
                return None
            time.sleep(self.delay * (attempt + 1))
        return None

    def extract_report_links(self, soup, source_url, series_info):
        """Extract all report links from a page"""
        report_links = []
        
        # Find all links on the page
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Check if it's a report link
            if 'report' in href.lower() or 'report' in text.lower():
                if href and not href.startswith('javascript:'):
                    try:
                        full_url = urljoin(self.base_url, href)
                        
                        # Extract additional info from the URL
                        match_id = self.extract_match_id_from_url(href)
                        season = self.extract_season_from_url(href, series_info)
                        
                        report_info = {
                            'text': text,
                            'url': full_url,
                            'match_id': match_id,
                            'series_name': series_info.get('text', ''),
                            'series_url': series_info.get('url', ''),
                            'season': season,
                            'source_page': source_url,
                            'scraped_at': datetime.now().isoformat()
                        }
                        
                        # Avoid duplicates
                        if report_info not in report_links:
                            report_links.append(report_info)
                            
                    except Exception as e:
                        logger.warning(f"Error processing report link: {e}")
                        continue
        
        return report_links

    def extract_match_id_from_url(self, url):
        """Extract match ID from URL"""
        try:
            # Match URLs typically have patterns like /series/id/team1-vs-team2-matchnum-matchid/
            parts = url.split('/')
            for part in parts:
                if part.isdigit() and len(part) >= 6:  # Match IDs are typically 6+ digits
                    return part
                # Sometimes match ID is at the end of a complex string
                if '-' in part and part.split('-')[-1].isdigit():
                    return part.split('-')[-1]
        except:
            pass
        return None

    def extract_season_from_url(self, url, series_info):
        """Extract season year from URL or series info"""
        try:
            # Try to extract from series name first
            series_name = series_info.get('text', '')
            for year in ['2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014', '2015', 
                        '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025']:
                if year in series_name:
                    return year
            
            # Try to extract from URL
            for year in ['2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014', '2015', 
                        '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025']:
                if year in url:
                    return year
        except:
            pass
        return 'unknown'

    def scrape_series_reports(self, series_info):
        """Scrape all report links from a single IPL series"""
        series_url = series_info['url']
        series_name = series_info['text']
        
        logger.info(f"🏏 Scraping reports from: {series_name}")
        
        response = self.get_page(series_url)
        if not response:
            logger.error(f"Failed to fetch series page: {series_url}")
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract report links from the main page
        report_links = self.extract_report_links(soup, series_url, series_info)
        
        # Look for additional pages that might contain more matches/reports
        # Common patterns: "View all matches", "Full fixtures", pagination
        additional_pages = []
        
        # Find links to other match-related pages
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True).lower()
            
            if any(keyword in text for keyword in ['view all', 'full fixtures', 'all matches', 'results']):
                if 'match' in href or 'result' in href or 'fixture' in href:
                    full_url = urljoin(self.base_url, href)
                    if full_url not in [series_url] and full_url not in additional_pages:
                        additional_pages.append(full_url)

        # Scrape additional pages
        for page_url in additional_pages[:3]:  # Limit to 3 additional pages per series
            logger.info(f"  📄 Scraping additional page: {page_url}")
            page_response = self.get_page(page_url)
            if page_response:
                page_soup = BeautifulSoup(page_response.content, 'html.parser')
                page_reports = self.extract_report_links(page_soup, page_url, series_info)
                report_links.extend(page_reports)

        # Remove duplicates
        unique_reports = []
        seen_urls = set()
        for report in report_links:
            if report['url'] not in seen_urls:
                unique_reports.append(report)
                seen_urls.add(report['url'])

        logger.info(f"  ✅ Found {len(unique_reports)} report links from {series_name}")
        return unique_reports

    def load_series_links(self, filename):
        """Load the 18 IPL series links from the previous scraper"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                series_data = json.load(f)
            logger.info(f"Loaded {len(series_data)} series links from {filename}")
            return series_data
        except FileNotFoundError:
            logger.error(f"Series links file not found: {filename}")
            return []
        except Exception as e:
            logger.error(f"Error loading series links: {e}")
            return []

    def save_reports(self, all_reports, filename_prefix):
        """Save all report links to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save to JSON
        json_filename = f"{filename_prefix}_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(all_reports, f, indent=2, ensure_ascii=False)
        
        # Save to CSV
        csv_filename = f"{filename_prefix}_{timestamp}.csv"
        if all_reports:
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                fieldnames = all_reports[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_reports)
        
        logger.info(f"Reports saved to {json_filename} and {csv_filename}")
        return json_filename, csv_filename

    def generate_summary(self, all_reports):
        """Generate summary statistics"""
        if not all_reports:
            return {}
        
        # Count by season
        season_counts = {}
        match_types = {}
        
        for report in all_reports:
            season = report.get('season', 'unknown')
            season_counts[season] = season_counts.get(season, 0) + 1
            
            # Try to determine match type from text
            text = report.get('text', '').lower()
            if 'final' in text:
                match_types['Final'] = match_types.get('Final', 0) + 1
            elif 'qualifier' in text:
                match_types['Qualifier'] = match_types.get('Qualifier', 0) + 1
            elif 'eliminator' in text:
                match_types['Eliminator'] = match_types.get('Eliminator', 0) + 1
            else:
                match_types['League'] = match_types.get('League', 0) + 1
        
        return {
            'total_reports': len(all_reports),
            'season_distribution': season_counts,
            'match_type_distribution': match_types,
            'unique_seasons': len(season_counts)
        }

def main():
    """Main function to scrape all IPL match reports"""
    scraper = IPLReportsScraper()
    
    print("🏏 IPL Match Reports Comprehensive Scraper")
    print("=" * 60)
    
    # Setup session
    scraper.setup_session()
    
    # Find the most recent series links file
    series_files = list(Path('.').glob('ipl_series_links_*.json'))
    if not series_files:
        print("❌ No IPL series links file found. Please run ipl_series_scraper.py first.")
        return
    
    # Use the most recent file
    latest_file = max(series_files, key=lambda p: p.stat().st_mtime)
    print(f"📁 Using series links from: {latest_file}")
    
    # Load the 18 IPL series
    series_list = scraper.load_series_links(latest_file)
    if not series_list:
        print("❌ Failed to load series links")
        return
    
    print(f"🎯 Found {len(series_list)} IPL series to scrape")
    
    # Scrape reports from each series
    all_reports = []
    failed_series = []
    
    for i, series_info in enumerate(series_list, 1):
        try:
            print(f"\n📊 Progress: {i}/{len(series_list)} - {series_info.get('text', 'Unknown')}")
            
            series_reports = scraper.scrape_series_reports(series_info)
            all_reports.extend(series_reports)
            
            print(f"   ✅ {len(series_reports)} reports found")
            
        except Exception as e:
            logger.error(f"Failed to scrape series {series_info.get('text', '')}: {e}")
            failed_series.append(series_info)
            continue
    
    # Save all reports
    if all_reports:
        json_file, csv_file = scraper.save_reports(all_reports, "ipl_all_match_reports")
        
        # Generate and display summary
        summary = scraper.generate_summary(all_reports)
        
        print(f"\n🎉 SCRAPING COMPLETED!")
        print(f"=" * 60)
        print(f"📊 Total match reports found: {summary['total_reports']}")
        print(f"🏆 Seasons covered: {summary['unique_seasons']}")
        
        print(f"\n📈 Reports by Season:")
        for season, count in sorted(summary['season_distribution'].items()):
            print(f"   {season}: {count} reports")
        
        print(f"\n🎯 Match Types:")
        for match_type, count in summary['match_type_distribution'].items():
            print(f"   {match_type}: {count} reports")
        
        if failed_series:
            print(f"\n⚠️  Failed to scrape {len(failed_series)} series:")
            for series in failed_series:
                print(f"   - {series.get('text', 'Unknown')}")
        
        print(f"\n💾 Files saved:")
        print(f"   📄 JSON: {json_file}")
        print(f"   📄 CSV: {csv_file}")
        
        # Sample report URLs
        print(f"\n🔗 Sample Report URLs:")
        for i, report in enumerate(all_reports[:10]):
            print(f"   {i+1}. {report['text']}")
            print(f"      {report['url']}")
    
    else:
        print("❌ No reports found")

if __name__ == "__main__":
    main()