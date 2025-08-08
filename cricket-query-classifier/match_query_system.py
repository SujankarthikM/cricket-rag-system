import pandas as pd
import re
from fuzzywuzzy import fuzz, process
from typing import List, Dict, Tuple
import os

class CricketMatchQuery:
    def __init__(self, data_dir="/Users/skarthikm/Documents/finalyear/cricket-query-classifier/matchspecific"):
        self.data_dir = data_dir
        self.load_data()
        
    def load_data(self):
        """Load all CSV files"""
        self.test_df = pd.read_csv(os.path.join(self.data_dir, "test.csv"))
        self.odi_df = pd.read_csv(os.path.join(self.data_dir, "odi.csv"))
        self.t20i_df = pd.read_csv(os.path.join(self.data_dir, "t20i.csv"))
        self.ipl_df = pd.read_csv(os.path.join(self.data_dir, "ipl.csv"))
        
        print(f"Loaded {len(self.test_df)} Test matches")
        print(f"Loaded {len(self.odi_df)} ODI matches") 
        print(f"Loaded {len(self.t20i_df)} T20I matches")
        print(f"Loaded {len(self.ipl_df)} IPL matches")
        
    def extract_teams_from_url(self, url: str) -> List[str]:
        """Extract team names from URL pattern"""
        # Pattern: team1-vs-team2 or team2-vs-team1
        pattern = r'/([a-zA-Z-]+)-vs-([a-zA-Z-]+)-'
        match = re.search(pattern, url)
        if match:
            team1 = match.group(1).replace('-', ' ').title()
            team2 = match.group(2).replace('-', ' ').title()
            return [team1, team2]
        return []
    
    def extract_match_number(self, url: str) -> str:
        """Extract match number from URL (1st, 2nd, final, etc.)"""
        patterns = [
            r'(\d+(?:st|nd|rd|th))-(?:test|odi|t20i|match)',
            r'(final|semi-final|qualifier)',
            r'(only)-(?:test|odi|t20i)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)
        return ""
    
    def get_match_ordinal(self, url: str) -> int:
        """Extract numeric ordinal from match (1st=1, 2nd=2, etc.)"""
        match_num = self.extract_match_number(url)
        if match_num:
            if match_num.lower() == 'only':
                return 1
            elif match_num.lower() in ['final', 'semi-final']:
                return 999  # High number for finals
            else:
                # Extract number from "1st", "2nd", etc.
                num_match = re.match(r'(\d+)', match_num)
                if num_match:
                    return int(num_match.group(1))
        return 0
    
    def parse_query(self, query: str) -> Dict:
        """Parse natural language query to extract components"""
        query_lower = query.lower()
        
        # Extract format
        format_type = "test"  # default
        if any(word in query_lower for word in ["odi", "one day"]):
            format_type = "odi"
        elif any(word in query_lower for word in ["t20", "twenty20"]):
            format_type = "t20i"
        elif any(word in query_lower for word in ["ipl", "indian premier league"]):
            format_type = "ipl"
        
        # Extract teams
        team_patterns = [
            r'(india|australia|england|pakistan|south africa|new zealand|sri lanka|bangladesh|zimbabwe|west indies)',
            r'(mumbai|chennai|bangalore|delhi|kolkata|punjab|rajasthan|hyderabad|deccan)'  # IPL teams
        ]
        
        teams = []
        for pattern in team_patterns:
            matches = re.findall(pattern, query_lower)
            teams.extend(matches)
        
        # Extract year
        year_match = re.search(r'\b(19|20)\d{2}(?:/\d{2})?\b', query)
        year = year_match.group(0) if year_match else ""
        
        # Extract match number - handle "last" specially
        match_number = ""
        if "last" in query_lower:
            match_number = "last"
        else:
            match_num_patterns = [
                r'\b(\d+(?:st|nd|rd|th))\s*(?:test|odi|t20|match)\b',
                r'\b(final|semi-final|qualifier|only)\b'
            ]
            
            for pattern in match_num_patterns:
                match = re.search(pattern, query_lower)
                if match:
                    match_number = match.group(1)
                    break
        
        return {
            "format": format_type,
            "teams": teams,
            "year": year,
            "match_number": match_number,
            "original_query": query
        }
    
    def score_match(self, row: pd.Series, parsed_query: Dict) -> float:
        """Score how well a match row matches the query"""
        score = 0.0
        
        # Series name fuzzy matching - boost for key terms like "ashes"
        if 'series_name' in row:
            series_name = str(row['series_name']).lower()
            query_lower = parsed_query["original_query"].lower()
            
            # Special boost for exact series matches
            if "ashes" in query_lower and "ashes" in series_name:
                score += 0.5
            elif "border gavaskar" in query_lower and "border" in series_name and "gavaskar" in series_name:
                score += 0.5
            else:
                series_score = fuzz.partial_ratio(query_lower, series_name) / 100.0
                score += series_score * 0.3
        
        # Team matching from URL
        url_teams = self.extract_teams_from_url(row['url'])
        if parsed_query["teams"] and url_teams:
            team_matches = 0
            for query_team in parsed_query["teams"]:
                for url_team in url_teams:
                    if fuzz.partial_ratio(query_team, url_team) > 70:
                        team_matches += 1
            score += (team_matches / max(len(parsed_query["teams"]), 1)) * 0.25
        
        # Year matching - more precise matching
        if parsed_query["year"]:
            year_found = False
            if 'series_name' in row and parsed_query["year"] in str(row['series_name']):
                score += 0.3
                year_found = True
            elif 'season' in row and parsed_query["year"] in str(row['season']):
                score += 0.3
                year_found = True
            
            # Penalty for wrong year
            if not year_found and parsed_query["year"]:
                if 'series_name' in row:
                    # Check if there's a different year in series name
                    other_years = re.findall(r'\b(19|20)\d{2}(?:/\d{2})?\b', str(row['series_name']))
                    if other_years and parsed_query["year"] not in other_years:
                        score -= 0.2
        
        # Match number matching - special handling for "last"
        if parsed_query["match_number"]:
            if parsed_query["match_number"] == "last":
                # For "last", we want the highest numbered match in the series
                url_match_ordinal = self.get_match_ordinal(row['url'])
                if url_match_ordinal > 0:
                    # Boost score for higher match numbers (5th > 4th > 3rd etc.)
                    score += min(url_match_ordinal * 0.02, 0.15)
            else:
                url_match_num = self.extract_match_number(row['url'])
                if url_match_num and fuzz.ratio(parsed_query["match_number"], url_match_num) > 80:
                    score += 0.15
        
        return score
    
    def search_matches(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for matches based on natural language query"""
        parsed_query = self.parse_query(query)
        
        # Select appropriate dataframe
        if parsed_query["format"] == "odi":
            df = self.odi_df
        elif parsed_query["format"] == "t20i":
            df = self.t20i_df
        elif parsed_query["format"] == "ipl":
            df = self.ipl_df
        else:
            df = self.test_df
        
        # Score all matches
        results = []
        for idx, row in df.iterrows():
            score = self.score_match(row, parsed_query)
            if score > 0.1:  # minimum threshold
                result = {
                    "url": row['url'],
                    "series_name": row.get('series_name', ''),
                    "season": row.get('season', ''),
                    "score": score,
                    "teams": self.extract_teams_from_url(row['url']),
                    "match_number": self.extract_match_number(row['url'])
                }
                results.append(result)
        
        # Sort by score and return top results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def query(self, user_query: str) -> None:
        """Main query function with formatted output"""
        print(f"\n🔍 Query: '{user_query}'")
        print("=" * 60)
        
        results = self.search_matches(user_query)
        
        if not results:
            print("❌ No matches found for your query.")
            return
        
        print(f"✅ Found {len(results)} matches:\n")
        
        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result['score']:.2f}")
            print(f"   Teams: {' vs '.join(result['teams']) if result['teams'] else 'N/A'}")
            print(f"   Series: {result['series_name']}")
            if result['season']:
                print(f"   Season: {result['season']}")
            if result['match_number']:
                print(f"   Match: {result['match_number']}")
            print(f"   URL: {result['url']}")
            print()

def main():
    # Initialize the query system
    query_system = CricketMatchQuery()
    
    print("\n🏏 Cricket Match Query System")
    print("=" * 40)
    
    # Test queries
    test_queries = [
        "last test ashes 2023",
        "5th test ashes 2023"
    ]
    
    for query in test_queries:
        query_system.query(query)
    
    # Interactive mode
    print("\n" + "="*60)
    print("🎯 Interactive Mode - Enter your queries (type 'quit' to exit):")
    print("="*60)
    
    while True:
        user_input = input("\n🏏 Enter your cricket match query: ").strip()
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        if user_input:
            query_system.query(user_input)

if __name__ == "__main__":
    main()