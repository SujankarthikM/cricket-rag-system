# test_fuzzy_name_matching.py
"""
Test fuzzy name matching for player names with career stats disambiguation.
Optimized version with batch queries.
"""
from rapidfuzz import process, fuzz
import sqlite3


def get_all_players_with_stats():
    """
    Get all players with their career statistics in one efficient query.
    Returns dict: {player_id: (name, full_name, country, stats)}
    """
    conn = sqlite3.connect('cricket_stats.db')
    cursor = conn.cursor()
    
    # Get all players first
    cursor.execute("SELECT player_id, name, full_name, country FROM players")
    players = {row[0]: {'name': row[1], 'full_name': row[2], 'country': row[3], 
                        'runs': 0, 'wickets': 0, 'matches': 0} 
               for row in cursor.fetchall()}
    
    # Aggregate batting stats (Test)
    cursor.execute("""
        SELECT player_id, COUNT(*), SUM(runs) 
        FROM test_batting 
        GROUP BY player_id
    """)
    for player_id, matches, runs in cursor.fetchall():
        if player_id in players:
            players[player_id]['matches'] += matches
            players[player_id]['runs'] += runs or 0
    
    # Aggregate batting stats (Whiteball)
    cursor.execute("""
        SELECT player_id, COUNT(*), SUM(runs) 
        FROM whiteball_batting 
        GROUP BY player_id
    """)
    
    for player_id, matches, runs in cursor.fetchall():
        if player_id in players:
            players[player_id]['matches'] += matches
            players[player_id]['runs'] += runs or 0
    
    # Aggregate bowling stats
    cursor.execute("""
        SELECT player_id, SUM(wickets) 
        FROM international_bowling 
        GROUP BY player_id
    """)
    for player_id, wickets in cursor.fetchall():
        if player_id in players:
            players[player_id]['wickets'] = wickets or 0
    
    conn.close()
    return players


def resolve_player_id(user_input, players_cache=None, show_all_matches=False):
    """
    Given a user input, find the best matching player name.
    Gets top 5 matches, then selects the one with most runs + wickets.
    
    Args:
        user_input: Name to search for
        players_cache: Pre-loaded players dict (for efficiency)
        show_all_matches: If True, print all top 5 matches
    
    Returns: (player_id, matched_name, score, full_name, country, stats, all_matches)
    """
    # Load players if not cached
    if players_cache is None:
        players_cache = get_all_players_with_stats()
    
    # Create list of (name_lower, player_id, player_data)
    player_list = [(data['name'].lower(), pid, data) 
                   for pid, data in players_cache.items()]
    
    all_names = [p[0] for p in player_list]
    
    # Get top 5 matches
    matches = process.extract(
        user_input.lower(), 
        all_names, 
        scorer=fuzz.token_sort_ratio,
        limit=5
    )
    
    if not matches:
        return None, None, 0, None, None, None, []
    
    # Build list of all matches with their stats
    all_match_details = []
    for match, score, idx in matches:
        _, player_id, data = player_list[idx]
        all_match_details.append({
            'player_id': player_id,
            'name': match,
            'score': score,
            'full_name': data['full_name'],
            'country': data['country'],
            'runs': data['runs'],
            'wickets': data['wickets'],
            'matches': data['matches'],
            'total_stats': data['runs'] + 30* data['wickets']  # Combined metric
        }) 
    
    # Sort by: 1) Total runs + wickets (descending), 2) Fuzzy score (descending)
    all_match_details.sort(key=lambda x: (x['total_stats'], x['score']), reverse=True)
    
    # Best match is the one with highest runs + wickets
    best = all_match_details[0]
    
    stats = {
        'runs': best['runs'], 
        'wickets': best['wickets'], 
        'matches': best['matches']
    }
    
    return (best['player_id'], best['name'], best['score'], 
            best['full_name'], best['country'], stats, all_match_details)


def display_player_info(user_input, players_cache, show_all=False):
    """Display matched player with their career stats."""
    result = resolve_player_id(user_input, players_cache)
    player_id, matched_name, score, full_name, country, stats, all_matches = result
    
    if player_id:
        print(f"\nInput: '{user_input}'")
        
        # Show all top 5 matches if requested
        if show_all and len(all_matches) > 1:
            print(f"\nTop 5 Matches (sorted by Runs + Wickets):")
            for i, match in enumerate(all_matches, 1):
                marker = "→ SELECTED" if i == 1 else ""
                print(f"{i}. {match['name'].title()} - Score: {match['score']} | "
                      f"Runs: {match['runs']:,} | Wickets: {match['wickets']} | "
                      f"Total: {match['total_stats']:,} {marker}")
            print()
        
        print(f"✓ Best Match: {matched_name.title()} (Fuzzy Score: {score})")
        print(f"  Full Name: {full_name}")
        print(f"  Country: {country}")
        print(f"  Player ID: {player_id}")
        if stats:
            print(f"  Career Stats:")
            print(f"    - Matches: {stats['matches']}")
            print(f"    - Runs: {stats['runs']:,}")
            print(f"    - Wickets: {stats['wickets']}")
            print(f"    - Total (Runs + Wickets): {stats['runs'] + 30 * stats['wickets']:,}")
    else:
        print(f"\nNo match found for '{user_input}'")
    print("-" * 60)


if __name__ == "__main__":
    print("Loading players and stats... (this may take a moment)")
    players_cache = get_all_players_with_stats()
    print(f"Loaded {len(players_cache)} players\n")
    
    test_inputs = [
        "Virat Kohli",
        "Kohli",
        "Rohit Sharma",
        "Sharma",
        "Kohli",
        "RG Sharma",
        "Sachin Tendulkar",
        "Tendulkar",
        "MS Dhoni",
        "Dhoni",
        "S Smith",
        "Anderson"
    ]
    
    # Show detailed view for ambiguous names
    print("=" * 60)
    print("DETAILED VIEW (showing all top 5 matches)")
    print("=" * 60)
    for inp in ["Tendulkar", "Smith", "Anderson", "Sharma"]:
        display_player_info(inp, players_cache, show_all=True)
    
    print("\n" + "=" * 60)
    print("QUICK VIEW (best match only)")
    print("=" * 60)
    for inp in test_inputs:
        display_player_info(inp, players_cache, show_all=False)