from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from .query_generator import generate_sql_query
from .database_executor import execute_query
from rapidfuzz import process, fuzz
def get_all_players_with_stats():
    conn = sqlite3.connect('cricket_stats.db')
    cursor = conn.cursor()
    cursor.execute("SELECT player_id, name, full_name, country FROM players")
    players = {row[0]: {'name': row[1], 'full_name': row[2], 'country': row[3], 'runs': 0, 'wickets': 0, 'matches': 0} for row in cursor.fetchall()}
    cursor.execute("SELECT player_id, COUNT(*), SUM(runs) FROM test_batting GROUP BY player_id")
    for player_id, matches, runs in cursor.fetchall():
        if player_id in players:
            players[player_id]['matches'] += matches
            players[player_id]['runs'] += runs or 0
    cursor.execute("SELECT player_id, COUNT(*), SUM(runs) FROM whiteball_batting GROUP BY player_id")
    for player_id, matches, runs in cursor.fetchall():
        if player_id in players:
            players[player_id]['matches'] += matches
            players[player_id]['runs'] += runs or 0
    cursor.execute("SELECT player_id, SUM(wickets) FROM international_bowling GROUP BY player_id")
    for player_id, wickets in cursor.fetchall():
        if player_id in players:
            players[player_id]['wickets'] = wickets or 0
    conn.close()
    return players




import re



def resolve_player_id_and_normalize_query(user_query, players_cache=None):
    """
    Extract quoted player name, fuzzy match to player_id using top-5 and stat-based disambiguation, and replace quoted name with player_id in the query.
    Returns: normalized_query, player_id, canonical_name
    """
    if players_cache is None:
        players_cache = get_all_players_with_stats()
    # Build a list of (name_lower, player_id, player_data)
    player_list = [(data['name'].lower(), pid, data) for pid, data in players_cache.items()]
    all_names = [p[0] for p in player_list]
    quoted = re.findall(r'"([^"]+)"|\'([^\']+)\'', user_query)
    if not quoted:
        return user_query, None, None
    phrase = (quoted[0][0] or quoted[0][1]).strip().lower()
    # Get top 5 matches
    matches = process.extract(phrase, all_names, scorer=fuzz.token_sort_ratio, limit=5)
    if not matches:
        return user_query, None, None
    # Build list of all matches with their stats
    all_match_details = []
    for match, score, idx in matches:
        _, player_id, data = player_list[idx]
        all_match_details.append({
            'player_id': player_id,
            'name': match,
            'score': score,
            'full_name': data.get('full_name'),
            'country': data.get('country'),
            'runs': data.get('runs', 0),
            'wickets': data.get('wickets', 0),
            'matches': data.get('matches', 0),
            'total_stats': data.get('runs', 0) + 30 * data.get('wickets', 0)
        })
    # Sort by: 1) Total runs + wickets (descending), 2) Fuzzy score (descending)
    all_match_details.sort(key=lambda x: (x['total_stats'], x['score']), reverse=True)
    best = all_match_details[0]
    player_id = best['player_id']
    canonical_name = best['name']
    # Replace all quoted occurrences (single or double) of the phrase with the player_id
    normalized_query = user_query
    for quote in ['"', "'"]:
        quoted_phrase = f'{quote}{quoted[0][0] or quoted[0][1]}{quote}'
        normalized_query = re.sub(re.escape(quoted_phrase), str(player_id), normalized_query, flags=re.IGNORECASE)
    return normalized_query, player_id, canonical_name

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
        players_cache = get_all_players_with_stats()
        # Try to resolve a player name to player_id
        normalized_query, player_id, canonical_name = resolve_player_id_and_normalize_query(request.query, players_cache)
        sql_query = await generate_sql_query(normalized_query)
        # If the SQL query still uses player_name, replace with player_id in WHERE clause
        if player_id and canonical_name and 'player_name' in sql_query:
            sql_query = sql_query.replace(f"player_name = '{canonical_name}'", f"player_id = {player_id}")
            sql_query = sql_query.replace(f"player_name = \"{canonical_name}\"", f"player_id = {player_id}")
        result = execute_query(sql_query)
        return {"sql_query": sql_query, "result": result, "normalized_query": normalized_query, "player_id": player_id, "canonical_name": canonical_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
