"""
ESPNCricinfo player statistics scraper
Extracts batting and bowling data for different cricket formats
"""
import requests
import json
import pandas as pd
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
import time
import os
from datetime import datetime

class CricinfoPlayerScraper:
    """Scraper for ESPNCricinfo player statistics"""
    
    def __init__(self, output_dir: str = "cricket_data"):
        self.base_url = "https://stats.espncricinfo.com/ci/engine/player"
        self.output_dir = output_dir
        self.session = requests.Session()
        
        # Set headers to mimic a browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Cricket format mapping
        self.formats = {
            1: "Test",
            2: "ODI", 
            3: "T20I",
            11: "First-class"
        }
        
        # Stat types
        self.stat_types = ["batting", "bowling"]
    
    def extract_player_data(self, player_id: int) -> Dict[str, Any]:
        """
        Extract complete player data for all formats and stat types
        
        Args:
            player_id: ESPNCricinfo player ID
            
        Returns:
            Dict containing all extracted data
        """
        print(f"🏏 Extracting data for player ID: {player_id}")
        
        player_data = {
            "player_id": player_id,
            "extraction_date": datetime.now().isoformat(),
            "formats": {}
        }
        
        # Extract data for each format and stat type
        for class_id, format_name in self.formats.items():
            print(f"  📊 Processing {format_name} (class={class_id})")
            player_data["formats"][format_name] = {}
            
            for stat_type in self.stat_types:
                print(f"    ⚾ Extracting {stat_type} data...")
                
                try:
                    stats_data = self._extract_stats_table(player_id, class_id, stat_type)
                    player_data["formats"][format_name][stat_type] = stats_data
                    
                    # Add small delay to be respectful
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"    ❌ Error extracting {stat_type} for {format_name}: {str(e)}")
                    player_data["formats"][format_name][stat_type] = {
                        "error": str(e),
                        "tables": []
                    }
        
        # Save the data
        self._save_player_data(player_id, player_data)
        
        return player_data
    
    def _extract_stats_table(self, player_id: int, class_id: int, stat_type: str) -> Dict[str, Any]:
        """
        Extract statistics table for specific format and type
        
        Args:
            player_id: Player ID
            class_id: Cricket format class (1=Test, 2=ODI, 3=T20I, 11=First-class)
            stat_type: "batting" or "bowling"
            
        Returns:
            Dict containing table data
        """
        # Build URL
        url = f"{self.base_url}/{player_id}.html"
        params = {
            "class": class_id,
            "template": "results",
            "type": stat_type,
            "view": "innings",
            "wrappertype": "print"
        }
        
        # Make request
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract tables
        tables_data = self._parse_tables(soup, stat_type)
        
        return {
            "url": response.url,
            "format": self.formats[class_id],
            "stat_type": stat_type,
            "tables": tables_data,
            "extraction_time": datetime.now().isoformat()
        }
    
    def _parse_tables(self, soup: BeautifulSoup, stat_type: str) -> List[Dict[str, Any]]:
        """
        Parse all tables from the HTML
        
        Args:
            soup: BeautifulSoup object
            stat_type: "batting" or "bowling"
            
        Returns:
            List of table data
        """
        tables_data = []
        
        # Find all tables
        tables = soup.find_all('table')
        
        for i, table in enumerate(tables):
            try:
                table_data = self._parse_single_table(table, f"table_{i}", stat_type)
                if table_data:
                    tables_data.append(table_data)
            except Exception as e:
                print(f"      ⚠️  Error parsing table {i}: {str(e)}")
                continue
        
        return tables_data
    
    def _parse_single_table(self, table, table_id: str, stat_type: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single table
        
        Args:
            table: BeautifulSoup table element
            table_id: Identifier for the table
            stat_type: "batting" or "bowling"
            
        Returns:
            Dict containing table data or None
        """
        # Get table caption/title
        caption = ""
        caption_elem = table.find('caption')
        if caption_elem:
            caption = caption_elem.get_text(strip=True)
        
        # Extract headers
        headers = []
        header_row = table.find('tr')
        if header_row:
            header_cells = header_row.find_all(['th', 'td'])
            headers = [cell.get_text(strip=True) for cell in header_cells]
        
        # Extract all rows
        rows = []
        for row in table.find_all('tr')[1:]:  # Skip header row
            cells = row.find_all(['td', 'th'])
            row_data = [cell.get_text(strip=True) for cell in cells]
            if row_data:  # Only add non-empty rows
                rows.append(row_data)
        
        # Skip empty tables
        if not headers or not rows:
            return None
        
        # Create structured data
        structured_rows = []
        for row in rows:
            if len(row) >= len(headers):
                row_dict = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        row_dict[header] = row[i]
                structured_rows.append(row_dict)
        
        return {
            "table_id": table_id,
            "caption": caption,
            "stat_type": stat_type,
            "headers": headers,
            "raw_rows": rows,
            "structured_rows": structured_rows,
            "row_count": len(rows)
        }
    
    def _save_player_data(self, player_id: int, data: Dict[str, Any]) -> None:
        """
        Save player data to JSON file
        
        Args:
            player_id: Player ID
            data: Player data to save
        """
        filename = f"player_{player_id}_stats.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved data to: {filepath}")
    
    def extract_multiple_players(self, player_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        Extract data for multiple players
        
        Args:
            player_ids: List of player IDs
            
        Returns:
            Dict mapping player IDs to their data
        """
        all_data = {}
        
        for i, player_id in enumerate(player_ids, 1):
            print(f"\\n🎯 Processing player {i}/{len(player_ids)}: {player_id}")
            
            try:
                player_data = self.extract_player_data(player_id)
                all_data[player_id] = player_data
                
                # Add delay between players
                if i < len(player_ids):
                    print("⏳ Waiting 3 seconds...")
                    time.sleep(3)
                    
            except Exception as e:
                print(f"❌ Failed to extract data for player {player_id}: {str(e)}")
                all_data[player_id] = {
                    "player_id": player_id,
                    "error": str(e),
                    "extraction_date": datetime.now().isoformat()
                }
        
        # Save combined data
        combined_file = os.path.join(self.output_dir, "all_players_data.json")
        with open(combined_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        
        print(f"\\n💾 Saved combined data to: {combined_file}")
        return all_data
    
    def get_player_summary(self, player_id: int) -> Dict[str, Any]:
        """
        Get a summary of extracted data for a player
        
        Args:
            player_id: Player ID
            
        Returns:
            Summary dict
        """
        filename = f"player_{player_id}_stats.json"
        filepath = os.path.join(self.output_dir, filename)
        
        if not os.path.exists(filepath):
            return {"error": "Player data not found"}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        summary = {
            "player_id": player_id,
            "extraction_date": data.get("extraction_date"),
            "formats_available": list(data.get("formats", {}).keys()),
            "total_tables": 0
        }
        
        # Count tables by format and type
        for format_name, format_data in data.get("formats", {}).items():
            for stat_type, stat_data in format_data.items():
                if isinstance(stat_data, dict) and "tables" in stat_data:
                    table_count = len(stat_data["tables"])
                    summary["total_tables"] += table_count
                    summary[f"{format_name}_{stat_type}_tables"] = table_count
        
        return summary

# Example usage and testing
if __name__ == "__main__":
    # Test with some popular player IDs
    test_player_ids = [
        253802
    ]
    
    scraper = CricinfoPlayerScraper()
    
    # Test with single player first
    print("🧪 Testing with single player...")
    kohli_data = scraper.extract_player_data(253802)
    
    # Show summary
    summary = scraper.get_player_summary(253802)
    print(f"\\n📊 Summary for player 253802:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\\n✅ Single player test completed!")
    print("\\nTo extract all test players, run:")
    print("scraper.extract_multiple_players(test_player_ids)")