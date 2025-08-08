"""
Cricket Database Query Executor
Executes SQL queries against the cricket database and returns results
"""
import sqlite3
import pandas as pd
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import os

class CricketQueryExecutor:
    """Execute SQL queries against the cricket database"""
    
    def __init__(self, db_path: str = "cricket_database.db"):
        self.db_path = db_path
        self.db_exists = os.path.exists(db_path)
    
    def execute_query(self, sql_query: str, return_format: str = "json") -> Dict[str, Any]:
        """
        Execute SQL query and return results
        
        Args:
            sql_query: SQL query to execute
            return_format: "json", "csv", "dataframe", "dict"
            
        Returns:
            Dict with query results and metadata
        """
        if not self.db_exists:
            return {
                "success": False,
                "error": "Database not found. Please create the database first.",
                "query": sql_query,
                "suggestion": "Run the data ingestion process to create the database"
            }
        
        try:
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            
            # Execute query and get results
            if return_format == "dataframe":
                df = pd.read_sql_query(sql_query, conn)
                result_data = df
                row_count = len(df)
            else:
                cursor = conn.cursor()
                cursor.execute(sql_query)
                
                # Get column names
                columns = [description[0] for description in cursor.description]
                
                # Get all rows
                rows = cursor.fetchall()
                row_count = len(rows)
                
                # Format results based on requested format
                if return_format == "json":
                    result_data = [dict(zip(columns, row)) for row in rows]
                elif return_format == "csv":
                    # Convert to pandas DataFrame first, then CSV
                    df = pd.DataFrame(rows, columns=columns)
                    result_data = df.to_csv(index=False)
                elif return_format == "dict":
                    result_data = {
                        "columns": columns,
                        "rows": rows
                    }
                else:
                    result_data = [dict(zip(columns, row)) for row in rows]
            
            conn.close()
            
            return {
                "success": True,
                "data": result_data,
                "row_count": row_count,
                "query": sql_query,
                "format": return_format,
                "execution_time": datetime.now().isoformat()
            }
            
        except sqlite3.Error as e:
            return {
                "success": False,
                "error": f"Database error: {str(e)}",
                "query": sql_query,
                "error_type": "database_error"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution error: {str(e)}",
                "query": sql_query,
                "error_type": "general_error"
            }
    
    def execute_multiple_queries(self, queries: List[str]) -> Dict[str, Any]:
        """
        Execute multiple queries in sequence
        
        Args:
            queries: List of SQL queries
            
        Returns:
            Results for all queries
        """
        results = []
        
        for i, query in enumerate(queries):
            print(f"Executing query {i+1}/{len(queries)}...")
            result = self.execute_query(query)
            results.append({
                "query_index": i,
                "query": query,
                "result": result
            })
        
        successful = sum(1 for r in results if r["result"]["success"])
        
        return {
            "total_queries": len(queries),
            "successful": successful,
            "failed": len(queries) - successful,
            "results": results,
            "execution_summary": f"{successful}/{len(queries)} queries executed successfully"
        }
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get information about a table structure
        
        Args:
            table_name: Name of the table
            
        Returns:
            Table structure information
        """
        if not self.db_exists:
            return {"error": "Database not found"}
        
        info_query = f"PRAGMA table_info({table_name})"
        result = self.execute_query(info_query)
        
        if result["success"]:
            return {
                "table_name": table_name,
                "columns": result["data"],
                "column_count": result["row_count"]
            }
        else:
            return {
                "error": f"Could not get info for table '{table_name}'",
                "details": result["error"]
            }
    
    def get_database_tables(self) -> Dict[str, Any]:
        """
        Get list of all tables in the database
        
        Returns:
            List of table names
        """
        if not self.db_exists:
            return {"error": "Database not found"}
        
        tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
        result = self.execute_query(tables_query)
        
        if result["success"]:
            table_names = [row["name"] for row in result["data"]]
            return {
                "tables": table_names,
                "table_count": len(table_names)
            }
        else:
            return {"error": "Could not retrieve table list"}
    
    def preview_table(self, table_name: str, limit: int = 5) -> Dict[str, Any]:
        """
        Get a preview of table data
        
        Args:
            table_name: Name of the table
            limit: Number of rows to return
            
        Returns:
            Sample data from the table
        """
        preview_query = f"SELECT * FROM {table_name} LIMIT {limit}"
        result = self.execute_query(preview_query)
        
        if result["success"]:
            return {
                "table_name": table_name,
                "sample_data": result["data"],
                "sample_size": result["row_count"],
                "preview_limit": limit
            }
        else:
            return {
                "error": f"Could not preview table '{table_name}'",
                "details": result["error"]
            }
    
    def export_query_results(self, sql_query: str, output_file: str, format: str = "csv") -> Dict[str, Any]:
        """
        Execute query and export results to file
        
        Args:
            sql_query: SQL query to execute
            output_file: Output file path
            format: Export format ("csv", "json", "excel")
            
        Returns:
            Export result
        """
        result = self.execute_query(sql_query, return_format="dataframe")
        
        if not result["success"]:
            return result
        
        try:
            df = result["data"]
            
            if format.lower() == "csv":
                df.to_csv(output_file, index=False)
            elif format.lower() == "json":
                df.to_json(output_file, orient="records", indent=2)
            elif format.lower() == "excel":
                df.to_excel(output_file, index=False)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported export format: {format}"
                }
            
            return {
                "success": True,
                "output_file": output_file,
                "format": format,
                "rows_exported": len(df),
                "query": sql_query
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Export failed: {str(e)}",
                "output_file": output_file
            }
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get overall database statistics
        
        Returns:
            Database statistics
        """
        if not self.db_exists:
            return {"error": "Database not found"}
        
        stats = {
            "database_path": self.db_path,
            "database_exists": True,
            "tables": {}
        }
        
        # Get table list
        tables_result = self.get_database_tables()
        if "error" in tables_result:
            return tables_result
        
        # Get stats for each table
        for table_name in tables_result["tables"]:
            count_query = f"SELECT COUNT(*) as row_count FROM {table_name}"
            count_result = self.execute_query(count_query)
            
            if count_result["success"]:
                row_count = count_result["data"][0]["row_count"]
                stats["tables"][table_name] = {
                    "row_count": row_count,
                    "structure": self.get_table_info(table_name)
                }
        
        return stats

# Mock executor for testing when database doesn't exist
class MockCricketQueryExecutor:
    """Mock executor that returns sample data when database doesn't exist"""
    
    def __init__(self):
        self.mock_data = self._get_mock_data()
    
    def _get_mock_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate mock cricket data for testing"""
        return {
            "kohli_odi_stats": [
                {
                    "full_name": "Virat Kohli",
                    "span": "2008-2023",
                    "mat": 274,
                    "runs": 12898,
                    "ave": 57.32,
                    "sr": 93.17,
                    "hundreds": 46,
                    "fifties": 65
                }
            ],
            "comparison_data": [
                {"full_name": "Virat Kohli", "runs": 12898},
                {"full_name": "Rohit Sharma", "runs": 9205}
            ]
        }
    
    def execute_query(self, sql_query: str, return_format: str = "json") -> Dict[str, Any]:
        """Mock execution that returns sample data"""
        query_lower = sql_query.lower()
        
        if "kohli" in query_lower and "odi" in query_lower:
            mock_result = self.mock_data["kohli_odi_stats"]
        elif any(name in query_lower for name in ["kohli", "rohit"]) and "runs" in query_lower:
            mock_result = self.mock_data["comparison_data"]
        else:
            mock_result = [{"message": "Mock data - database not ready yet"}]
        
        return {
            "success": True,
            "data": mock_result,
            "row_count": len(mock_result),
            "query": sql_query,
            "format": return_format,
            "is_mock": True,
            "note": "This is mock data. Real database not created yet."
        }

# Test the executor
if __name__ == "__main__":
    # Test with mock executor (when database doesn't exist)
    print("🏏 Testing Cricket Query Executor (Mock Mode)")
    
    mock_executor = MockCricketQueryExecutor()
    
    test_queries = [
        "SELECT full_name, runs FROM career_stats WHERE full_name LIKE '%Kohli%' AND format = 'odi'",
        "SELECT full_name, runs FROM career_stats WHERE full_name IN ('Virat Kohli', 'Rohit Sharma') ORDER BY runs DESC"
    ]
    
    for query in test_queries:
        print(f"\\n📊 Query: {query}")
        result = mock_executor.execute_query(query)
        
        if result["success"]:
            print(f"✅ Result: {result['data']}")
            print(f"Rows: {result['row_count']}")
        else:
            print(f"❌ Error: {result['error']}")
    
    print("\\n✅ Mock testing completed!")
    print("\\n📝 To use with real database:")
    print("  1. Create the database from extracted JSON data")
    print("  2. Use CricketQueryExecutor instead of MockCricketQueryExecutor")