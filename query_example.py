import sqlite3
from rapidfuzz import process


def get_player_runs(query_name, player_stats):
    # Get the best match from the keys of player_stats
    best_match, score, _ = process.extractOne(query_name, player_stats.keys())
    print(f"Best match: {best_match} (Score: {score})")
    return player_stats[best_match]

def get_player_id_by_name(db_path, query_name):
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch all player names and ids
    cursor.execute("SELECT player_id, player_name FROM players")
    players = cursor.fetchall()
    conn.close()

    # Build a mapping: name -> id
    name_to_id = {name: pid for pid, name in players}

    # Fuzzy match the query_name to player_name
    best_match, score, _ = process.extractOne(query_name, name_to_id.keys())
    print(f"Best match: {best_match} (Score: {score})")
    return name_to_id[best_match]

# Example usage
user_input = "Joe Root"

db_path = "D:\cricket-rag-system-new\cricket_stats.db"  # Replace with your actual database file path
player_id = get_player_id_by_name(db_path, user_input)
print(f"Player ID for {user_input}: {player_id}")