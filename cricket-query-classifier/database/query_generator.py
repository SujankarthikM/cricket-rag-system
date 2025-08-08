"""
Cricket Database Query Generator
Converts natural language requests to SQL queries based on cricket database schema
"""
import json
from typing import Dict, Any, List
from services.llm_service import LLMService

class CricketQueryGenerator:
    """Generate SQL queries for cricket database based on natural language input"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.schema = self._get_database_schema()
    
    def _get_database_schema(self) -> Dict[str, Any]:
        """Define the cricket database schema"""
        return {
            "tables": {
                "player_profile": {
                    "description": "Basic player information and profile details",
                    "columns": [
                        "cricinfo_id (PRIMARY KEY) - Unique player identifier",
                        "full_name - Player's complete name",
                        "born - Birth date/year",
                        "batting_style - Left/Right handed batting",
                        "nationality - Country of origin",
                        "bowling_style - Bowling type (pace/spin/etc)",
                        "playing_role - Batsman/Bowler/All-rounder/Wicket-keeper"
                    ]
                },
                "career_stats": {
                    "description": "Career statistics across all formats",
                    "columns": [
                        "cricinfo_id - Player identifier (FOREIGN KEY)",
                        "span - Career span (e.g., '2008-2023')",
                        "mat - Matches played",
                        "inns - Innings batted",
                        "no - Not out innings",
                        "runs - Total runs scored",
                        "hs - Highest score",
                        "ave - Batting average",
                        "bf - Balls faced",
                        "sr - Strike rate",
                        "hundreds - Number of centuries (100+)",
                        "fifties - Number of half-centuries (50+)",
                        "zeros - Number of ducks (0 runs)",
                        "fours - Number of boundaries (4s)",
                        "sixes - Number of sixes (6s)",
                        "format - Cricket format (test/odi/t20i/ipl)"
                    ]
                },
                "all_odi_innings": {
                    "description": "Individual ODI innings details",
                    "columns": [
                        "cricinfo_id - Player identifier",
                        "runs - Runs scored in innings",
                        "mins - Minutes batted",
                        "bf - Balls faced",
                        "fours - Boundaries in innings",
                        "sixes - Sixes in innings", 
                        "sr - Strike rate for innings",
                        "pos - Batting position",
                        "dismissal - How player got out",
                        "inns - Innings number in match",
                        "opposition - Opponent team",
                        "ground - Venue/stadium",
                        "start_date - Match start date"
                    ]
                },
                "all_test_innings": {
                    "description": "Individual Test innings details",
                    "columns": "Same schema as all_odi_innings"
                },
                "all_t20i_innings": {
                    "description": "Individual T20I innings details", 
                    "columns": "Same schema as all_odi_innings"
                },
                "all_ipl_innings": {
                    "description": "Individual IPL innings details",
                    "columns": "Same schema as all_odi_innings"
                }
            },
            "relationships": [
                "player_profile.cricinfo_id = career_stats.cricinfo_id",
                "player_profile.cricinfo_id = all_*_innings.cricinfo_id"
            ]
        }
    
    async def generate_sql_query(self, natural_language_request: str) -> Dict[str, Any]:
        """
        Convert natural language request to SQL query
        
        Args:
            natural_language_request: User's request in plain English
            
        Returns:
            Dict containing SQL query and metadata
        """
        
        prompt = f"""
You are a cricket database SQL query generator. Convert the natural language request to a SQL query using the provided schema.

DATABASE SCHEMA:
{json.dumps(self.schema, indent=2)}

NATURAL LANGUAGE REQUEST: "{natural_language_request}"

INSTRUCTIONS:
1. Analyze the request to understand what data is needed
2. Identify which tables to use based on the request
3. Generate appropriate SQL query with proper JOINs if needed
4. Use meaningful aliases for tables
5. Include proper WHERE clauses for filtering
6. Add ORDER BY for logical sorting
7. Use LIMIT if the query might return too many rows

RESPONSE FORMAT (JSON only):
{{
    "sql_query": "SELECT ... FROM ... WHERE ...",
    "tables_used": ["table1", "table2"],
    "query_type": "aggregation|filtering|comparison|ranking",
    "explanation": "Brief explanation of what the query does",
    "estimated_result": "Description of expected results",
    "columns_returned": ["column1", "column2"],
    "requires_joins": true/false
}}

EXAMPLES:

Request: "Get Virat Kohli's ODI career stats"
Response:
{{
    "sql_query": "SELECT p.full_name, c.span, c.mat, c.runs, c.ave, c.sr, c.hundreds, c.fifties FROM player_profile p JOIN career_stats c ON p.cricinfo_id = c.cricinfo_id WHERE p.full_name LIKE '%Kohli%' AND c.format = 'odi'",
    "tables_used": ["player_profile", "career_stats"],
    "query_type": "filtering",
    "explanation": "Retrieves Virat Kohli's ODI career statistics",
    "estimated_result": "Single row with Kohli's ODI career numbers",
    "columns_returned": ["full_name", "span", "mat", "runs", "ave", "sr", "hundreds", "fifties"],
    "requires_joins": true
}}

Request: "Who scored more ODI runs - Kohli or Rohit?"
Response:
{{
    "sql_query": "SELECT p.full_name, c.runs FROM player_profile p JOIN career_stats c ON p.cricinfo_id = c.cricinfo_id WHERE (p.full_name LIKE '%Kohli%' OR p.full_name LIKE '%Rohit%') AND c.format = 'odi' ORDER BY c.runs DESC",
    "tables_used": ["player_profile", "career_stats"],
    "query_type": "comparison", 
    "explanation": "Compares ODI runs between Kohli and Rohit Sharma",
    "estimated_result": "Two rows showing runs for both players, ordered by highest runs",
    "columns_returned": ["full_name", "runs"],
    "requires_joins": true
}}

Generate SQL query for the given request:
"""

        try:
            # Get LLM response
            response = await self.llm_service.classify_query(prompt)
            
            if response["success"]:
                return {
                    "success": True,
                    "query_data": response["data"],
                    "llm_usage": response.get("usage", {}),
                    "provider": response.get("provider", "unknown")
                }
            else:
                return {
                    "success": False,
                    "error": response["error"],
                    "fallback_query": self._generate_fallback_query(natural_language_request)
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Query generation failed: {str(e)}",
                "fallback_query": self._generate_fallback_query(natural_language_request)
            }
    
    def _generate_fallback_query(self, request: str) -> Dict[str, Any]:
        """Generate a basic fallback query when LLM fails"""
        request_lower = request.lower()
        
        # Simple keyword-based fallback
        if any(word in request_lower for word in ["kohli", "virat"]):
            player_filter = "full_name LIKE '%Kohli%'"
        elif any(word in request_lower for word in ["rohit", "sharma"]):
            player_filter = "full_name LIKE '%Rohit%'"
        elif any(word in request_lower for word in ["dhoni", "ms"]):
            player_filter = "full_name LIKE '%Dhoni%'"
        else:
            player_filter = "1=1"  # No filter
        
        if "odi" in request_lower:
            format_filter = "format = 'odi'"
        elif "test" in request_lower:
            format_filter = "format = 'test'"
        elif "t20" in request_lower:
            format_filter = "format = 't20i'"
        else:
            format_filter = "1=1"  # No format filter
        
        return {
            "sql_query": f"SELECT p.full_name, c.* FROM player_profile p JOIN career_stats c ON p.cricinfo_id = c.cricinfo_id WHERE {player_filter} AND {format_filter} LIMIT 10",
            "tables_used": ["player_profile", "career_stats"],
            "query_type": "fallback",
            "explanation": "Fallback query based on keyword matching",
            "estimated_result": "Basic player statistics",
            "columns_returned": ["full_name", "career_stats.*"],
            "requires_joins": True,
            "is_fallback": True
        }
    
    def validate_sql_query(self, sql_query: str) -> Dict[str, Any]:
        """
        Validate SQL query structure (basic checks)
        
        Args:
            sql_query: SQL query string
            
        Returns:
            Validation result
        """
        issues = []
        
        # Basic validation checks
        sql_upper = sql_query.upper()
        
        if not sql_upper.startswith("SELECT"):
            issues.append("Query must start with SELECT")
        
        if "FROM" not in sql_upper:
            issues.append("Query must include FROM clause")
        
        # Check for dangerous operations
        dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER", "INSERT", "UPDATE"]
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                issues.append(f"Dangerous operation detected: {keyword}")
        
        # Check table names
        valid_tables = list(self.schema["tables"].keys())
        for table in valid_tables:
            if table.replace("_", "") in sql_query.replace("_", ""):
                break
        else:
            issues.append("Query should reference valid table names")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "query": sql_query
        }
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Return the complete database schema"""
        return self.schema
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get information about a specific table"""
        if table_name in self.schema["tables"]:
            return self.schema["tables"][table_name]
        else:
            return {"error": f"Table '{table_name}' not found in schema"}

# Test the query generator
if __name__ == "__main__":
    import asyncio
    
    async def test_query_generator():
        generator = CricketQueryGenerator()
        
        test_requests = [
            "Get Virat Kohli's ODI career stats",
            "Who scored more ODI runs - Kohli or Rohit?",
            "Show me Dhoni's best Test innings",
            "Compare strike rates of Kohli in all formats",
            "List all centuries by Rohit Sharma in ODIs"
        ]
        
        for request in test_requests:
            print(f"\\n🔍 Request: {request}")
            print("-" * 50)
            
            result = await generator.generate_sql_query(request)
            
            if result["success"]:
                query_data = result["query_data"]
                print(f"SQL: {query_data['sql_query']}")
                print(f"Type: {query_data['query_type']}")
                print(f"Tables: {query_data['tables_used']}")
                print(f"Explanation: {query_data['explanation']}")
            else:
                print(f"Error: {result['error']}")
                if 'fallback_query' in result:
                    print(f"Fallback SQL: {result['fallback_query']['sql_query']}")
    
    asyncio.run(test_query_generator())