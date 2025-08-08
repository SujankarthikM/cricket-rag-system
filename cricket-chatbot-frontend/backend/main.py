from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
import os

# Add the path to the cricket-query-classifier directory
sys.path.append('/Users/skarthikm/Documents/finalyear/cricket-query-classifier')

# Import our match query system
from match_query_system import CricketMatchQuery

app = FastAPI(title="Cricket Match Query API", description="API for querying cricket matches")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the query system
query_system = CricketMatchQuery()

class QueryRequest(BaseModel):
    query: str

class MatchResult(BaseModel):
    url: str
    series_name: str
    season: Optional[str] = ""
    score: float
    teams: List[str]
    match_number: str

class QueryResponse(BaseModel):
    matches: List[MatchResult]
    query: str
    total_results: int

@app.get("/")
async def root():
    return {"message": "Cricket Match Query API is running!"}

@app.post("/search", response_model=QueryResponse)
async def search_matches(request: QueryRequest):
    try:
        # Use our existing query system
        results = query_system.search_matches(request.query, top_k=5)
        
        # Convert results to the expected format
        matches = []
        for result in results:
            match = MatchResult(
                url=result["url"],
                series_name=result["series_name"],
                season=result.get("season", ""),
                score=result["score"],
                teams=result["teams"],
                match_number=result["match_number"]
            )
            matches.append(match)
        
        return QueryResponse(
            matches=matches,
            query=request.query,
            total_results=len(matches)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "total_matches": {
        "test": len(query_system.test_df),
        "odi": len(query_system.odi_df), 
        "t20i": len(query_system.t20i_df),
        "ipl": len(query_system.ipl_df)
    }}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)