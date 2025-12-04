import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
import sqlite3

def create_database(db_path):
    """
    Creates the SQLite database and tables for storing cricket stats.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Players Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS players (
            player_id INTEGER PRIMARY KEY,
            player_name TEXT NOT NULL UNIQUE
        )
    ''')

    # International Batting Stats
    c.execute('''
        CREATE TABLE IF NOT EXISTS international_batting (
            player_id INTEGER,
            format TEXT,
            batting_pos TEXT,
            dismissal BOOLEAN,
            runs INTEGER,
            balls_faced INTEGER,
            strike_rate REAL,
            fours INTEGER,
            sixes INTEGER,
            opposition TEXT,
            ground TEXT,
            start_date DATE,
            match_url TEXT,
            FOREIGN KEY (player_id) REFERENCES players (player_id)
        )
    ''')

    # International Bowling Stats
    c.execute('''
        CREATE TABLE IF NOT EXISTS international_bowling (
            player_id INTEGER,
            format TEXT,
            overs REAL,
            maidens INTEGER,
            runs_conceded INTEGER,
            wickets INTEGER,
            economy REAL,
            average REAL,
            strike_rate REAL,
            opposition TEXT,
            ground TEXT,
            start_date DATE,
            match_url TEXT,
            FOREIGN KEY (player_id) REFERENCES players (player_id)
        )
    ''')

    # IPL Batting Stats
    c.execute('''
        CREATE TABLE IF NOT EXISTS ipl_batting (
            player_id INTEGER,
            runs INTEGER,
            not_out BOOLEAN,
            balls_faced INTEGER,
            strike_rate REAL,
            fours INTEGER,
            sixes INTEGER,
            opposition TEXT,
            ground TEXT,
            start_date DATE,
            match_url TEXT,
            FOREIGN KEY (player_id) REFERENCES players (player_id)
        )
    ''')

    # IPL Bowling Stats
    c.execute('''
        CREATE TABLE IF NOT EXISTS ipl_bowling (
            player_id INTEGER,
            overs REAL,
            maidens INTEGER,
            runs_conceded INTEGER,
            wickets INTEGER,
            economy REAL,
            average REAL,
            strike_rate REAL,
            opposition TEXT,
            ground TEXT,
            start_date DATE,
            match_url TEXT,
            FOREIGN KEY (player_id) REFERENCES players (player_id)
        )
    ''')

    conn.commit()
    return conn

def process_and_store_data(conn, table, url, player_id, player_name, is_batting=True, is_ipl=False):
    """
    Parses HTML table data and stores it in the database.
    """
    # Add player to players table
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO players (player_id, player_name) VALUES (?, ?)", (player_id, player_name))
    conn.commit()

    headers = [th.get_text(strip=True) for th in table.find_all('th')]
    headers[-1] = "matchid"
    opposition_index = headers.index('Opposition') if 'Opposition' in headers else -1

    if opposition_index == -1:
        print("Could not find 'Opposition' header.")
        return

    opposition_teams = [
        'vCSK', 'vMI', 'vRR', 'vKKR', 'vPunjab Kings', 'vLSG', 'vGT', 'vSRH', 'vDC', 'vRCB',
        'vKings XI', 'vDaredevils', 'vGuj Lions', 'vSupergiants', 'vChargers', 'vWarriors', 'vKochi'
    ]

    data_rows = []
    for row in table.find_all('tr'):
        cells = row.find_all(['td', 'th'])
        if not cells or len(cells) < opposition_index + 3:
            continue
        columns = [cell.get_text(strip=True) for cell in cells]
        if columns[0] in ('Bat1', 'Overs', 'Match'):
            continue
        
        stat_columns = columns[1:opposition_index]
        is_empty_row_data = all((c.strip() == '-' or c.strip() == '' or c.strip() == '—') for c in stat_columns)
        if is_empty_row_data:
            continue

        opposition_value = columns[opposition_index]
        match_url = urljoin(url, cells[-1].find('a')['href']) if cells[-1].find('a') else "No URL"
        
        if is_ipl:
            if opposition_value not in opposition_teams:
                continue
            if is_batting:
                runs_str = columns[0]
                not_out = '*' in runs_str
                runs = runs_str.replace('*', '')
                data_rows.append([player_id, runs, not_out, columns[2], columns[3], columns[4], columns[5], columns[7], columns[8], columns[9], match_url])
            else: # IPL Bowling
                data_rows.append([player_id, columns[0], columns[1], columns[2], columns[3], columns[4], columns[5], columns[6],  columns[8], columns[9], columns[10], match_url])

        else: # International
            match_format = opposition_value.split(' ')[0] if ' ' in opposition_value else ''
            if is_batting:
                dismissal = '*' not in columns[0]
                data_rows.append([player_id, match_format, columns[0], dismissal, columns[2], columns[3], columns[4], columns[5], columns[6], columns[8], columns[9], columns[10], match_url])
            else: # International Bowling
                data_rows.append([player_id, match_format, columns[0], columns[1], columns[2], columns[3], columns[4], columns[5], columns[6],  columns[8], columns[9], columns[10], match_url])

    if not data_rows:
        print("No data processed.")
        return

    if is_ipl:
        if is_batting:
            df = pd.DataFrame(data_rows, columns=['player_id', 'runs', 'not_out', 'balls_faced', 'strike_rate', 'fours', 'sixes', 'opposition', 'ground', 'start_date', 'match_url'])
            df['runs'] = pd.to_numeric(df['runs'], errors='coerce')
            df['not_out'] = df['not_out'].astype(bool)
            df['balls_faced'] = pd.to_numeric(df['balls_faced'], errors='coerce')
            df['strike_rate'] = pd.to_numeric(df['strike_rate'], errors='coerce')
            df['fours'] = pd.to_numeric(df['fours'], errors='coerce')
            df['sixes'] = pd.to_numeric(df['sixes'], errors='coerce')
            df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce').dt.date
            df.to_sql('ipl_batting', conn, if_exists='append', index=False)
        else:
            df = pd.DataFrame(data_rows, columns=['player_id', 'overs', 'maidens', 'runs_conceded', 'wickets', 'economy', 'average', 'strike_rate', 'opposition', 'ground', 'start_date', 'match_url'])
            df['overs'] = pd.to_numeric(df['overs'], errors='coerce')
            df['maidens'] = pd.to_numeric(df['maidens'], errors='coerce')
            df['runs_conceded'] = pd.to_numeric(df['runs_conceded'], errors='coerce')
            df['wickets'] = pd.to_numeric(df['wickets'], errors='coerce')
            df['economy'] = pd.to_numeric(df['economy'], errors='coerce')
            df['average'] = pd.to_numeric(df['average'], errors='coerce')
            df['strike_rate'] = pd.to_numeric(df['strike_rate'], errors='coerce')
            df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce').dt.date
            df.to_sql('ipl_bowling', conn, if_exists='append', index=False)
    else:
        if is_batting:
            df = pd.DataFrame(data_rows, columns=['player_id', 'format', 'batting_pos', 'dismissal', 'runs', 'balls_faced', 'strike_rate', 'fours', 'sixes', 'opposition', 'ground', 'start_date', 'match_url'])
            df['runs'] = pd.to_numeric(df['runs'], errors='coerce')
            df['dismissal'] = df['dismissal'].astype(bool)
            df['balls_faced'] = pd.to_numeric(df['balls_faced'], errors='coerce')
            df['strike_rate'] = pd.to_numeric(df['strike_rate'], errors='coerce')
            df['fours'] = pd.to_numeric(df['fours'], errors='coerce')
            df['sixes'] = pd.to_numeric(df['sixes'], errors='coerce')
            df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce').dt.date
            df.to_sql('international_batting', conn, if_exists='append', index=False)
        else:
            df = pd.DataFrame(data_rows, columns=['player_id', 'format', 'overs', 'maidens', 'runs_conceded', 'wickets', 'economy', 'average', 'strike_rate', 'opposition', 'ground', 'start_date', 'match_url'])
            df['overs'] = pd.to_numeric(df['overs'], errors='coerce')
            df['maidens'] = pd.to_numeric(df['maidens'], errors='coerce')
            df['runs_conceded'] = pd.to_numeric(df['runs_conceded'], errors='coerce')
            df['wickets'] = pd.to_numeric(df['wickets'], errors='coerce')
            df['economy'] = pd.to_numeric(df['economy'], errors='coerce')
            df['average'] = pd.to_numeric(df['average'], errors='coerce')
            df['strike_rate'] = pd.to_numeric(df['strike_rate'], errors='coerce')
            df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce').dt.date
            df.to_sql('international_bowling', conn, if_exists='append', index=False)
    
    print(f"--- Stored {'Batting' if is_batting else 'Bowling'} data for {'IPL' if is_ipl else 'International'} ---")

def scrape_and_store_tables(conn, url, player_id, player_name, is_ipl=False, is_batting=True):
    """
    Scrapes tables from a URL and triggers the data storage process.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        tables = soup.find_all('table', class_='engineTable')

        if tables and len(tables) >= 4:
            process_and_store_data(conn, tables[3], url, player_id, player_name, is_batting=is_batting, is_ipl=is_ipl)
        else:
            print(f"Required tables not found on {url}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    import csv
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import time

    db_path = 'cricket_stats.db'
    # Create the database and tables once before threads start
    conn = create_database(db_path)
    conn.close()

    def scrape_player(player_id, player_name):
        print(f"[START] Player: {player_name} (ID: {player_id})")
        db_path = 'cricket_stats.db'
        conn = create_database(db_path)
        for x in [11, 6]:  # Class: 11 for T20I/ODI combined, 6 for IPL
            is_ipl = (x == 6)
            for y in ["batting", "bowling"]:
                is_batting = (y == "batting")
                url = f"https://stats.espncricinfo.com/ci/engine/player/{player_id}.html?class={x};template=results;type={y};view=match"
                print(f"[FETCH] {player_name} ({player_id}) | {y} | {'IPL' if is_ipl else 'International'} | URL: {url}")
                max_retries = 10
                delay = 2
                for attempt in range(max_retries):
                    try:
                        scrape_and_store_tables(conn, url, player_id, player_name, is_ipl=is_ipl, is_batting=is_batting)
                        print(f"[SUCCESS] {player_name} ({player_id}) | {y} | {'IPL' if is_ipl else 'International'}")
                        break
                    except Exception as e:
                        print(f"[RETRY] {player_name} ({player_id}) | {y} | Attempt {attempt+1}/10 | Error: {e}")
                        time.sleep(delay)
                        continue
        conn.close()
        print(f"[DONE] Player: {player_name} (ID: {player_id})")

    players = []
    with open('unique_fielding_players.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            players.append((row['Player ID'], row['Player Name']))

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(scrape_player, pid, pname) for pid, pname in players]
        completed = 0
        total = len(futures)
        for future in as_completed(futures):
            completed += 1
            print(f"[PROGRESS] {completed}/{total} players completed.")

    print("\nScript finished. Database is populated.")