import sqlite3
import os

# Assuming cricket_stats.db is in the root directory
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'cricket_stats.db')

def execute_query(sql_query: str):
    """
    Executes a SQL query on the SQLite database and returns the result.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query)
            
            # For SELECT statements, fetch the results
            if sql_query.strip().upper().startswith("SELECT"):
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                return {"columns": columns, "rows": rows}
            # For other statements (INSERT, UPDATE, DELETE), commit the changes
            else:
                conn.commit()
                return {"status": "success", "rows_affected": cursor.rowcount}
    except sqlite3.Error as e:
        return {"error": str(e)}

if __name__ == '__main__':
    # For testing the database executor
    # Replace with a valid query for your database
    test_query = "SELECT player_name, runs FROM batting_stats ORDER BY runs DESC LIMIT 5;"
    results = execute_query(test_query)
    print(f"Executing query: {test_query}")
    print("Results:")
    print(results)

    # Example of a query that might be generated
    test_query_2 = "SELECT COUNT(*) FROM matches;"
    results_2 = execute_query(test_query_2)
    print(f"Executing query: {test_query_2}")
    print("Results:")
    print(results_2)
