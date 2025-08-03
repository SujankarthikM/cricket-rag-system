#!/usr/bin/env python3
"""
ESPNCricinfo 2025 Season Scraper
Scrapes basic cricket series and match data from ESPNCricinfo
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import csv
from datetime import datetime
from urllib.parse import urljoin, urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ESPNCricinfoScraper:
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
        self.delay = 2  # Respectful delay between requests
        
    def get_page(self, url, retries=3):
        """Fetch a page with error handling and retries"""
        for attempt in range(retries):
            try:
                logger.info(f"Fetching: {url} (Attempt {attempt + 1})")
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                time.sleep(self.delay)  # Respectful delay
                return response
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == retries - 1:
                    logger.error(f"Failed to fetch {url} after {retries} attempts")
                    return None
                time.sleep(self.delay * (attempt + 1))  # Exponential backoff
        return None

    def scrape_series_for_reports(self, series_url, max_pages=5):
        """Scrape individual series pages to find more report links"""
        all_reports = []
        
        response = self.get_page(series_url)
        if not response:
            logger.warning(f"Failed to fetch series page: {series_url}")
            return []
            
        soup = BeautifulSoup(response.content, 'html.parser')
        reports = self.extract_report_links(soup)
        all_reports.extend(reports)
        
        # Look for pagination or match list pages
        match_schedule_links = soup.find_all('a', href=lambda x: x and 'match-schedule' in x)
        for link in match_schedule_links[:max_pages]:
            schedule_url = urljoin(self.base_url, link.get('href'))
            schedule_response = self.get_page(schedule_url)
            if schedule_response:
                schedule_soup = BeautifulSoup(schedule_response.content, 'html.parser')
                schedule_reports = self.extract_report_links(schedule_soup)
                all_reports.extend(schedule_reports)
        
        # Remove duplicates
        unique_reports = []
        seen_urls = set()
        for report in all_reports:
            if report['url'] not in seen_urls:
                unique_reports.append(report)
                seen_urls.add(report['url'])
        
        logger.info(f"Found {len(unique_reports)} unique reports from series: {series_url}")
        return unique_reports

    def scrape_2025_season(self):
        """Scrape 2025 season overview page"""
        url = "https://www.espncricinfo.com/ci/engine/series/index.html?season=2025;view=season"
        response = self.get_page(url)
        
        if not response:
            logger.error("Failed to fetch 2025 season page")
            return {}

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract series data
        series_data = self.extract_series_data(soup)
        
        # Extract match data
        matches_data = self.extract_matches_data(soup)
        
        # Extract report links
        report_links = self.extract_report_links(soup)
        
        return {
            'season': '2025',
            'url': url,
            'scraped_at': datetime.now().isoformat(),
            'series': series_data,
            'matches': matches_data,
            'report_links': report_links
        }

    def extract_series_data(self, soup):
        """Extract series information from the page"""
        series_list = []
        
        # Look for series containers (these selectors might need adjustment)
        series_containers = soup.find_all(['div', 'section'], class_=lambda x: x and ('series' in x.lower() or 'tournament' in x.lower()))
        
        # Alternative: Look for links with series patterns
        series_links = soup.find_all('a', href=lambda x: x and '/series/' in x)
        
        for link in series_links[:20]:  # Limit to first 20 series
            try:
                series_info = {
                    'name': link.get_text(strip=True),
                    'url': urljoin(self.base_url, link.get('href')),
                    'series_id': self.extract_series_id(link.get('href'))
                }
                if series_info['name'] and series_info not in series_list:
                    series_list.append(series_info)
            except Exception as e:
                logger.warning(f"Error extracting series info: {e}")
                continue
                
        logger.info(f"Found {len(series_list)} series")
        return series_list

    def extract_matches_data(self, soup):
        """Extract match information from the page"""
        matches_list = []
        
        # Look for match links
        match_links = soup.find_all('a', href=lambda x: x and ('/match/' in x or '/scorecard/' in x))
        
        for link in match_links[:50]:  # Limit to first 50 matches
            try:
                match_info = {
                    'title': link.get_text(strip=True),
                    'url': urljoin(self.base_url, link.get('href')),
                    'match_id': self.extract_match_id(link.get('href'))
                }
                if match_info['title'] and match_info not in matches_list:
                    matches_list.append(match_info)
            except Exception as e:
                logger.warning(f"Error extracting match info: {e}")
                continue
                
        logger.info(f"Found {len(matches_list)} matches")
        return matches_list

    def extract_report_links(self, soup):
        """Extract all report links from the page"""
        report_links = []
        
        # Look for links containing "report" in href or text
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True).lower()
            
            # Check if it's a report link
            if ('/report/' in href or 'report' in text.lower()) and href:
                try:
                    report_info = {
                        'text': link.get_text(strip=True),
                        'url': urljoin(self.base_url, href),
                        'match_id': self.extract_match_id_from_report(href),
                        'series_id': self.extract_series_id_from_report(href)
                    }
                    
                    # Avoid duplicates
                    if report_info not in report_links and report_info['url'] != self.base_url:
                        report_links.append(report_info)
                        
                except Exception as e:
                    logger.warning(f"Error extracting report link: {e}")
                    continue
        
        logger.info(f"Found {len(report_links)} report links")
        return report_links

    def extract_match_id_from_report(self, href):
        """Extract match ID from report URL"""
        try:
            # Report URLs often have pattern: /series/id/report/match_id/title
            if '/report/' in href:
                parts = href.split('/report/')
                if len(parts) > 1:
                    # Get the part after /report/
                    after_report = parts[1].split('/')[0]
                    if after_report.isdigit():
                        return after_report
        except:
            pass
        return None

    def extract_series_id_from_report(self, href):
        """Extract series ID from report URL"""
        try:
            # Report URLs often have pattern: /series/series_id/report/match_id/title
            if '/series/' in href:
                parts = href.split('/series/')
                if len(parts) > 1:
                    series_part = parts[1].split('/')[0]
                    if series_part.isdigit():
                        return series_part
        except:
            pass
        return None

    def extract_series_id(self, href):
        """Extract series ID from URL"""
        try:
            if '/series/' in href:
                # Extract ID from URL pattern like /series/name-id/
                parts = href.split('/series/')[-1].split('/')
                if parts and '-' in parts[0]:
                    return parts[0].split('-')[-1]
        except:
            pass
        return None

    def extract_match_id(self, href):
        """Extract match ID from URL"""
        try:
            if '/match/' in href:
                # Extract ID from URL pattern like /match/id/
                parts = href.split('/match/')[-1].split('/')
                if parts and parts[0].isdigit():
                    return parts[0]
        except:
            pass
        return None

    def scrape_live_scores(self):
        """Scrape current live scores"""
        url = "https://www.espncricinfo.com/live-cricket-score"
        response = self.get_page(url)
        
        if not response:
            logger.error("Failed to fetch live scores page")
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        live_matches = []
        
        # Look for live match containers
        match_containers = soup.find_all(['div', 'section'], class_=lambda x: x and 'match' in x.lower())
        
        for container in match_containers[:10]:  # Limit to first 10 live matches
            try:
                # Extract basic match info
                match_info = {
                    'teams': self.extract_teams(container),
                    'scores': self.extract_scores(container),
                    'status': self.extract_match_status(container),
                    'scraped_at': datetime.now().isoformat()
                }
                live_matches.append(match_info)
            except Exception as e:
                logger.warning(f"Error extracting live match: {e}")
                continue
                
        logger.info(f"Found {len(live_matches)} live matches")
        return live_matches

    def extract_teams(self, container):
        """Extract team names from match container"""
        teams = []
        # Look for team name patterns
        team_elements = container.find_all(['span', 'div'], class_=lambda x: x and 'team' in x.lower())
        for elem in team_elements:
            team_name = elem.get_text(strip=True)
            if team_name and len(team_name) > 1:
                teams.append(team_name)
        return teams[:2]  # Limit to 2 teams

    def extract_scores(self, container):
        """Extract scores from match container"""
        scores = []
        # Look for score patterns (numbers followed by slash and numbers)
        score_elements = container.find_all(text=lambda x: x and '/' in str(x))
        for score in score_elements:
            score_text = str(score).strip()
            if score_text and any(char.isdigit() for char in score_text):
                scores.append(score_text)
        return scores

    def extract_match_status(self, container):
        """Extract match status"""
        # Look for status indicators
        status_keywords = ['live', 'completed', 'upcoming', 'innings', 'over']
        text = container.get_text().lower()
        for keyword in status_keywords:
            if keyword in text:
                return keyword
        return 'unknown'

    def save_data(self, data, filename):
        """Save scraped data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Data saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save data: {e}")

    def save_to_csv(self, data, filename):
        """Save data to CSV format"""
        try:
            if 'series' in data and data['series']:
                with open(f"series_{filename}", 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=['name', 'url', 'series_id'])
                    writer.writeheader()
                    writer.writerows(data['series'])
                    
            if 'matches' in data and data['matches']:
                with open(f"matches_{filename}", 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=['title', 'url', 'match_id'])
                    writer.writeheader()
                    writer.writerows(data['matches'])
                    
            if 'report_links' in data and data['report_links']:
                with open(f"reports_{filename}", 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=['text', 'url', 'match_id', 'series_id'])
                    writer.writeheader()
                    writer.writerows(data['report_links'])
                    
            logger.info(f"CSV data saved with prefix: {filename}")
        except Exception as e:
            logger.error(f"Failed to save CSV: {e}")

def main():
    """Main function to run the scraper"""
    scraper = ESPNCricinfoScraper()
    
    logger.info("Starting ESPNCricinfo scraper...")
    
    # Scrape 2025 season data
    logger.info("Scraping 2025 season data...")
    season_data = scraper.scrape_2025_season()
    
    if season_data:
        # Save to JSON
        scraper.save_data(season_data, 'espncricinfo_2025_season.json')
        
        # Save to CSV
        scraper.save_to_csv(season_data, 'espncricinfo_2025.csv')
        
        # Print summary
        print(f"\n=== Scraping Summary ===")
        print(f"Season: {season_data.get('season', 'N/A')}")
        print(f"Series found: {len(season_data.get('series', []))}")
        print(f"Matches found: {len(season_data.get('matches', []))}")
        print(f"Report links found: {len(season_data.get('report_links', []))}")
        print(f"Data saved to: espncricinfo_2025_season.json")
    
    # Scrape live scores
    logger.info("Scraping live scores...")
    live_data = scraper.scrape_live_scores()
    
    if live_data:
        scraper.save_data(live_data, 'espncricinfo_live_scores.json')
        print(f"Live matches found: {len(live_data)}")
        print(f"Live data saved to: espncricinfo_live_scores.json")
    
    # Deep scrape for more report links
    logger.info("Deep scraping series for more report links...")
    if season_data and season_data.get('series'):
        all_deep_reports = []
        # Scrape top 5 series for more reports
        for series in season_data['series'][:5]:
            if series.get('url') and series.get('series_id'):
                deep_reports = scraper.scrape_series_for_reports(series['url'])
                all_deep_reports.extend(deep_reports)
        
        if all_deep_reports:
            scraper.save_data(all_deep_reports, 'espncricinfo_deep_reports.json')
            
            # Save to CSV
            with open('deep_reports_espncricinfo_2025.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['text', 'url', 'match_id', 'series_id'])
                writer.writeheader()
                writer.writerows(all_deep_reports)
                
            print(f"Deep report links found: {len(all_deep_reports)}")
            print(f"Deep reports saved to: espncricinfo_deep_reports.json")
    
    logger.info("Scraping completed!")

if __name__ == "__main__":
    main()