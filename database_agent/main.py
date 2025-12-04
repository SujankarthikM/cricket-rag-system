from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from .query_generator import generate_sql_query
from .database_executor import execute_query

app = FastAPI(
    title="Database Agent",
    description="An agent that converts natural language queries to SQL and executes them.",
    version="1.0.0"
)

class QueryRequest(BaseModel):
    query: str

@app.post("/query")
async def process_query(request: QueryRequest):
    try:
        # Generate SQL query
        sql_query = await generate_sql_query(request.query)

        # Execute the query
        result = execute_query(sql_query)

        return {"sql_query": sql_query, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
