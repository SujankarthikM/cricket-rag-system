import sqlite3
import os
import json
from .services.llm_service import LLMService

# Assuming cricket_stats.db is in the root directory
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'cricket_stats.db')

def get_database_schema():
    """Reads the schema of the SQLite database."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            schema = {}
            for table in tables:
                table_name = table[0]
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                schema[table_name] = [col[1] for col in columns]
            return schema
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None

async def generate_sql_query(natural_language_query: str) -> str:
    """
    Generates an SQL query from a natural language query using an LLM.
    """
    schema = get_database_schema()
    if not schema:
        return "Error: Could not get database schema."

    schema_representation = "\n".join([f"- {table}: {', '.join(columns)}" for table, columns in schema.items()])

    prompt = f"""
    Given the following database schema:
    {schema_representation}

    Translate the following natural language query into a SQL query:
    "{natural_language_query}"

    Return the result as a JSON object with a single key "sql_query".
    For example:
    {{
        "sql_query": "SELECT * FROM players;"
    }}
    """
    print(prompt)

    llm_service = LLMService()
    response = await llm_service.classify_query(prompt)

    print("LLM Response:", response)  # Logging the raw response

    if response["success"]:
        try:
            data = response.get("data", {})
            if isinstance(data, str):
                data = json.loads(data)
            
            sql_query = data.get("sql_query")

            if sql_query:
                return sql_query
            else:
                return f"Error: Could not extract SQL query from LLM response. Response data: {response['data']}"

        except (json.JSONDecodeError, TypeError):
            # Fallback for when the response is not a valid JSON string
            if 'raw_content' in response:
                raw_content = response['raw_content']
                if 'SELECT' in raw_content:
                    return raw_content.strip()
            return f"Error: Could not parse LLM response as JSON. Raw content: {response.get('raw_content', '')}"
    else:
        return f"Error: LLM service failed with error: {response['error']}"

if __name__ == '__main__':
    # For testing the query generator
    import asyncio
    
    async def test():
        query = "Who has the highest score in all matches?"
        sql = await generate_sql_query(query)
        print(f"Natural Language Query: {query}")
        print(f"Generated SQL: {sql}")

    asyncio.run(test())
