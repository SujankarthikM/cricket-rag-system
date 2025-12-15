#!/usr/bin/env python3
"""
ESPNCricinfo Live Score Scraper
Extracts content from divs with class "ds-px-4 ds-py-3"
"""
import requests
from bs4 import BeautifulSoup
import time
import random
import json
from typing import Dict, List, Any

class CricinfoLiveScraper:
    """Scraper for ESPNCricinfo live scores"""
    
    def __init__(self):
        self.session = requests.Session()
        
        # Multiple user agents to rotate
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        ]
        
        # Set initial headers
        self._set_headers()
    
    def _set_headers(self):
        """Set realistic headers"""
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        self.session.headers.update(headers)
    
    def scrape_live_scores(self, url: str = "https://www.espncricinfo.com/cricketers/brian-masaba-420492") -> Dict[str, Any]:
        """
        Scrape live cricket scores from ESPNCricinfo
        
        Args:
            url: ESPNCricinfo URL to scrape
            
        Returns:
            Dict containing scraped data
        """
        print(f"🏏 Scraping: {url}")
        
        try:
            # Add random delay to appear human-like
            time.sleep(random.uniform(1, 3))
            
            # Make request
            response = self.session.get(url, timeout=15)
            
            print(f"Response Status: {response.status_code}")
            
            if response.status_code == 403:
                print("❌ 403 Forbidden - Website is blocking the request")
                return self._handle_403_error(url)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "url": url
                }
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract target divs
            target_divs = soup.find_all('div', class_='ds-px-4 ds-py-3')
            
            print(f"Found {len(target_divs)} divs with class 'ds-px-4 ds-py-3'")
            
            if not target_divs:
                # Try alternative class names that might be similar
                alternative_classes = [
                    'ds-px-4',
                    'ds-py-3', 
                    'ds-p-4',
                    'match-info',
                    'live-score'
                ]
                
                for alt_class in alternative_classes:
                    alt_divs = soup.find_all('div', class_=alt_class)
                    if alt_divs:
                        print(f"Found {len(alt_divs)} divs with alternative class '{alt_class}'")
                        target_divs = alt_divs
                        break
            
            # Extract content from divs
            extracted_data = self._extract_div_content(target_divs)
            
            return {
                "success": True,
                "url": url,
                "total_divs_found": len(target_divs),
                "extracted_data": extracted_data,
                "page_title": soup.title.string if soup.title else "No title",
                "scrape_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "url": url,
                "error_type": "network_error"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Scraping failed: {str(e)}",
                "url": url,
                "error_type": "parsing_error"
            }
    
    def _extract_div_content(self, divs: List) -> List[Dict[str, Any]]:
        """
        Extract content from target divs
        
        Args:
            divs: List of BeautifulSoup div elements
            
        Returns:
            List of extracted content
        """
        extracted_content = []
        
        for i, div in enumerate(divs):
            try:
                div_data = {
                    "div_index": i,
                    "full_text": div.get_text(strip=True),
                    "html_content": str(div),
                    "child_elements": [],
                    "links": [],
                    "images": []
                }
                
                # Extract child elements
                for child in div.children:
                    if hasattr(child, 'name') and child.name:
                        child_text = child.get_text(strip=True)
                        if child_text:
                            div_data["child_elements"].append({
                                "tag": child.name,
                                "text": child_text,
                                "classes": child.get('class', [])
                            })
                
                # Extract links
                links = div.find_all('a', href=True)
                for link in links:
                    div_data["links"].append({
                        "text": link.get_text(strip=True),
                        "href": link['href']
                    })
                
                # Extract images
                images = div.find_all('img', src=True)
                for img in images:
                    div_data["images"].append({
                        "alt": img.get('alt', ''),
                        "src": img['src']
                    })
                
                # Look for cricket-specific content
                div_data["cricket_content"] = self._identify_cricket_content(div)
                
                extracted_content.append(div_data)
                
            except Exception as e:
                extracted_content.append({
                    "div_index": i,
                    "error": f"Failed to extract: {str(e)}",
                    "raw_html": str(div)[:200]  # First 200 chars
                })
        
        return extracted_content
    
    def _identify_cricket_content(self, div) -> Dict[str, Any]:
        """
        Identify cricket-specific content in the div
        
        Args:
            div: BeautifulSoup div element
            
        Returns:
            Dict containing cricket-specific content
        """
        text = div.get_text(strip=True).lower()
        cricket_content = {
            "has_scores": False,
            "has_teams": False,
            "has_overs": False,
            "has_wickets": False,
            "teams_found": [],
            "scores_found": [],
            "match_status": ""
        }
        
        # Look for scores (pattern: number/number)
        import re
        score_pattern = r'\b\d+/\d+\b'
        scores = re.findall(score_pattern, text)
        if scores:
            cricket_content["has_scores"] = True
            cricket_content["scores_found"] = scores
        
        # Look for overs (pattern: number.number overs)
        overs_pattern = r'\b\d+\.\d+\s*overs?\b'
        overs = re.findall(overs_pattern, text)
        if overs:
            cricket_content["has_overs"] = True
        
        # Look for team names
        common_teams = [
            'india', 'australia', 'england', 'south africa', 'new zealand',
            'pakistan', 'sri lanka', 'bangladesh', 'west indies', 'afghanistan'
        ]
        
        for team in common_teams:
            if team in text:
                cricket_content["has_teams"] = True
                cricket_content["teams_found"].append(team.title())
        
        # Look for match status keywords
        status_keywords = ['live', 'innings break', 'stumps', 'lunch', 'tea', 'rain', 'match delayed']
        for keyword in status_keywords:
            if keyword in text:
                cricket_content["match_status"] = keyword
                break
        
        return cricket_content
    
    def _handle_403_error(self, url: str) -> Dict[str, Any]:
        """
        Handle 403 Forbidden error
        
        Args:
            url: URL that returned 403
            
        Returns:
            Error response with suggestions
        """
        return {
            "success": False,
            "error": "403 Forbidden - Access denied",
            "url": url,
            "error_type": "access_denied",
            "suggestions": [
                "Use VPN to change IP address",
                "Try accessing from different network",
                "Use browser automation (Selenium) instead",
                "Try alternative cricket websites",
                "Use official cricket APIs",
                "Add more realistic headers and delays"
            ],
            "alternative_approach": "Consider using Selenium WebDriver for better success"
        }
    
    def save_results(self, results: Dict[str, Any], filename: str = "cricinfo_live_data.json"):
        """
        Save scraping results to JSON file
        
        Args:
            results: Scraping results
            filename: Output filename
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"💾 Results saved to: {filename}")
        except Exception as e:
            print(f"❌ Failed to save results: {str(e)}")

def main():
    """Main function to run the scraper"""
    print("🏏 ESPNCricinfo Live Score Scraper")
    print("=" * 40)
    
    scraper = CricinfoLiveScraper()
    
    # Scrape the live scores page
    results = scraper.scrape_live_scores()
    
    if results["success"]:
        print(f"✅ Scraping successful!")
        print(f"📊 Found {results['total_divs_found']} divs with target class")
        print(f"📄 Page title: {results['page_title']}")
        
        # Display first few results
        for i, div_data in enumerate(results["extracted_data"][:3]):
            print(f"\\n🎯 Div {i+1}:")
            print(f"   Text: {div_data['full_text'][:100]}...")
            
            if div_data.get("cricket_content", {}).get("has_scores"):
                print(f"   ⚾ Cricket scores found: {div_data['cricket_content']['scores_found']}")
            
            if div_data.get("cricket_content", {}).get("teams_found"):
                print(f"   🏏 Teams: {div_data['cricket_content']['teams_found']}")
        
        # Save results
        scraper.save_results(results)
        
    else:
        print(f"❌ Scraping failed: {results['error']}")
        
        if results.get("error_type") == "access_denied":
            print("\\n💡 Suggestions:")
            for suggestion in results.get("suggestions", []):
                print(f"   • {suggestion}")
        
        print(f"\\n🔧 Alternative: {results.get('alternative_approach', 'Try different approach')}")

if __name__ == "__main__":
    main()