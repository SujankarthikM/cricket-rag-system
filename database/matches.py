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

    # Players Table (expanded to include all columns from unique_fielding_players.csv)
    c.execute('''
        CREATE TABLE IF NOT EXISTS players (
            player_id INTEGER PRIMARY KEY,
            player_name TEXT NOT NULL,
            name TEXT,
            country TEXT,
            full_name TEXT,
            playing_role TEXT,
            batting_style TEXT,
            bowling_style TEXT
        )
    ''')

    # Test Batting Stats (new schema)
    c.execute('''
        CREATE TABLE IF NOT EXISTS test_batting (
            player_id INTEGER,
            first_innings INTEGER,
            second_innings INTEGER,
            runs INTEGER,
            balls_faced INTEGER,
            strike_rate REAL,
            fours INTEGER,
            sixes INTEGER,
            opposition TEXT,
            ground TEXT,
            start_date DATE,
            match_url TEXT,
            dismissal_1st BOOLEAN,
            dismissal_2nd BOOLEAN,
            FOREIGN KEY (player_id) REFERENCES players (player_id)
        )
    ''')

    # Whiteball Batting Stats (ODI/T20I)
    c.execute('''
        CREATE TABLE IF NOT EXISTS whiteball_batting (
            player_id INTEGER,
            format TEXT,
            runs INTEGER,
            dismissal BOOLEAN,
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

def process_and_store_data(conn, table, url, player_id, player_name, class_id=None, match_format=None, is_batting=True, is_ipl=False):
    """
    Parses HTML table data and stores it in the database.
    """
    # Add player to players table (with all columns)
    c = conn.cursor()
    # Try to get player details from unique_fielding_players.csv
    import csv
    player_details = None
    try:
        with open('unique_fielding_players.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if str(row['Player ID']) == str(player_id):
                    player_details = row
                    break
    except Exception as e:
        print(f"Error reading player details: {e}")

    if player_details:
        c.execute("""
            INSERT OR IGNORE INTO players (
                player_id, player_name, name, country, full_name, playing_role, batting_style, bowling_style
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            player_id,
            player_details.get('Player Name', player_name),
            player_details.get('NAME'),
            player_details.get('COUNTRY'),
            player_details.get('Full name'),
            player_details.get('Playing role'),
            player_details.get('Batting style'),
            player_details.get('Bowling style')
        ))
    else:
        # Fallback: only player_id and player_name
        c.execute("INSERT OR IGNORE INTO players (player_id, player_name) VALUES (?, ?)", (player_id, player_name))
    conn.commit()

    try:
        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        headers[-1] = "matchid"
        opposition_index = headers.index('Opposition') if 'Opposition' in headers else -1
    except Exception as e:
        print(f"Error processing headers for player_id={player_id}, player_name={player_name}: {e}")
        return

    if opposition_index == -1:
        print(f"Could not find 'Opposition' header for player_id={player_id}, player_name={player_name}.")
        return

    opposition_teams = [
        'vCSK', 'vMI', 'vRR', 'vKKR', 'vPunjab Kings', 'vLSG', 'vGT', 'vSRH', 'vDC', 'vRCB',
        'vKings XI', 'vDaredevils', 'vGuj Lions', 'vSupergiants', 'vChargers', 'vWarriors', 'vKochi'
    ]

    data_rows = []
    for row in table.find_all('tr'):
        try:
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
                    opp = columns[7].split("v", 1)[-1]
                    data_rows.append([player_id, runs, not_out, columns[2], columns[3], columns[4], columns[5], opp, columns[8], columns[9], match_url])
                else:  # IPL Bowling
                    opp = columns[-4].split("v", 1)[-1]
                    data_rows.append([player_id, columns[0], columns[-11], columns[-10], columns[-9], columns[-8], columns[-7], columns[-6], opp, columns[-3], columns[-2], match_url])

            else:  # International
                # Use explicit class_id and match_format
                if class_id == 1:
                    match_format = "Test"
                elif class_id == 2:
                    match_format = "ODI"
                elif class_id == 3:
                    match_format = "T20I"
                else:
                    match_format = "Unknown"
                if is_batting:
                    if match_format == "Test":
                        try:
                            opp_idx = None
                            for idx in range(len(columns)-1, -1, -1):
                                if columns[idx].startswith('v'):
                                    opp_idx = idx
                                    break
                            if opp_idx is None or opp_idx < 4:
                                continue
                            match_url = urljoin(url, cells[-1].find('a')['href']) if cells[-1].find('a') else "No URL"
                            ground = columns[opp_idx+1] if len(columns) > opp_idx+1 else None
                            start_date = columns[opp_idx+2] if len(columns) > opp_idx+2 else None
                            opp = columns[opp_idx].split('v',1)[-1].strip()
                            def parse_innings(val):
                                if val is None or val.strip() == '-' or val.strip() == '':
                                    return None, None
                                val = val.strip()
                                dismissal = not ('*' in val)
                                val = val.replace('*','')
                                try:
                                    return int(val), dismissal
                                except:
                                    return None, dismissal
                            first_innings, dismissal_1st = parse_innings(columns[0]) if len(columns) > 0 else (None, None)
                            second_innings, dismissal_2nd = parse_innings(columns[1]) if len(columns) > 1 else (None, None)
                            runs = 0
                            valid = False
                            for inn in [first_innings, second_innings]:
                                if inn is not None:
                                    runs += inn
                                    valid = True
                            if not valid:
                                continue
                            balls_faced = columns[3] if len(columns) > 3 else None
                            strike_rate = columns[4] if len(columns) > 4 else None
                            fours = columns[5] if len(columns) > 5 else None
                            sixes = columns[6] if len(columns) > 6 else None
                            data_rows.append([
                                player_id,
                                first_innings,
                                second_innings,
                                runs,
                                balls_faced,
                                strike_rate,
                                fours,
                                sixes,
                                opp,
                                ground,
                                start_date,
                                match_url,
                                dismissal_1st,
                                dismissal_2nd
                            ])
                        except Exception as e:
                            print(f"Error parsing Test batting row for player_id={player_id}, player_name={player_name}: {e}")
                            continue
                    elif match_format in ("ODI", "T20I"):
                        dismissal = '*' not in columns[0]
                        opp = columns[-4].split('v')[-1]
                        data_rows.append([player_id, match_format, columns[-10], dismissal, columns[-9], columns[-8], columns[-7], columns[-6], opp, columns[-3], columns[-2], match_url])
                else:  # International Bowling
                    opp = columns[8].split('v')[-1]
                    data_rows.append([player_id, match_format, columns[0], columns[1], columns[2], columns[3], columns[4], columns[5], columns[6], opp, columns[9], columns[10], match_url])
        except Exception as e:
            print(f"Error processing row for player_id={player_id}, player_name={player_name}: {e}")
            continue

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
            if class_id == 1:
                # Test Batting (new schema)
                df = pd.DataFrame(data_rows, columns=[
                    'player_id',
                    'first_innings',
                    'second_innings',
                    'runs',
                    'balls_faced',
                    'strike_rate',
                    'fours',
                    'sixes',
                    'opposition',
                    'ground',
                    'start_date',
                    'match_url',
                    'dismissal_1st',
                    'dismissal_2nd'
                ])
                df['first_innings'] = pd.to_numeric(df['first_innings'], errors='coerce')
                df['second_innings'] = pd.to_numeric(df['second_innings'], errors='coerce')
                df['runs'] = pd.to_numeric(df['runs'], errors='coerce')
                df['balls_faced'] = pd.to_numeric(df['balls_faced'], errors='coerce')
                df['strike_rate'] = pd.to_numeric(df['strike_rate'], errors='coerce')
                df['fours'] = pd.to_numeric(df['fours'], errors='coerce')
                df['sixes'] = pd.to_numeric(df['sixes'], errors='coerce')
                df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce').dt.date
                df.to_sql('test_batting', conn, if_exists='append', index=False)
            elif class_id in (2, 3):
                # Whiteball Batting (ODI/T20I)
                df = pd.DataFrame(data_rows, columns=['player_id', 'format', 'runs', 'dismissal', 'balls_faced', 'strike_rate', 'fours', 'sixes', 'opposition', 'ground', 'start_date', 'match_url'])
                df['runs'] = pd.to_numeric(df['runs'], errors='coerce')
                df['dismissal'] = df['dismissal'].astype(bool)
                df['balls_faced'] = pd.to_numeric(df['balls_faced'], errors='coerce')
                df['strike_rate'] = pd.to_numeric(df['strike_rate'], errors='coerce')
                df['fours'] = pd.to_numeric(df['fours'], errors='coerce')
                df['sixes'] = pd.to_numeric(df['sixes'], errors='coerce')
                df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce').dt.date
                df.to_sql('whiteball_batting', conn, if_exists='append', index=False)
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
    print(f"--- Stored {'Batting' if is_batting else 'Bowling'} data for {'IPL' if is_ipl else match_format} ---")

def scrape_and_store_tables(conn, url, player_id, player_name, class_id=None, match_format=None, is_ipl=False, is_batting=True):
    """
    Scrapes tables from a URL and triggers the data storage process.
    """
    import time
    max_retries = 5
    delay = 3
    log_file = 'scrape_errors.log'
    for attempt in range(1, max_retries + 1):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            tables = soup.find_all('table', class_='engineTable')

            # Extract class id from url (class=1,2,3,6)
            import re
            match = re.search(r'class=(\d+)', url)
            this_class_id = int(match.group(1)) if match else class_id
            # Set match_format
            if this_class_id == 1:
                this_match_format = "Test"
            elif this_class_id == 2:
                this_match_format = "ODI"
            elif this_class_id == 3:
                this_match_format = "T20I"
            elif this_class_id == 6:
                this_match_format = "IPL"
            else:
                this_match_format = "Unknown"

            if tables and len(tables) >= 4:
                process_and_store_data(conn, tables[3], url, player_id, player_name, class_id=this_class_id, match_format=this_match_format, is_batting=is_batting, is_ipl=is_ipl)
            else:
                msg = f"Required tables not found on {url} (Player: {player_name}, ID: {player_id})\n"
                print(msg.strip())
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"[TABLE ERROR] {msg}")
            break
        except requests.exceptions.RequestException as e:
            msg = f"[FETCH ERROR] Attempt {attempt}/{max_retries} | Player: {player_name} (ID: {player_id}) | URL: {url} | Error: {e}\n"
            print(msg.strip())
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(msg)
            if attempt == max_retries:
                print(f"[FAILED] Max retries reached for {player_name} (ID: {player_id}) | URL: {url}")
            else:
                time.sleep(delay)
                continue
        except Exception as e:
            msg = f"[GENERAL ERROR] Attempt {attempt}/{max_retries} | Player: {player_name} (ID: {player_id}) | URL: {url} | Error: {e}\n"
            print(msg.strip())
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(msg)
            if attempt == max_retries:
                print(f"[FAILED] Max retries reached for {player_name} (ID: {player_id}) | URL: {url}")
            else:
                time.sleep(delay)
                continue
        break

if __name__ == '__main__':
    import csv
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import time

    db_path = 'cricket_stats.db'
    # Create the database and tables once before threads start
    ''''''
    conn = create_database(db_path)
    conn.close()

    def scrape_player(player_id, player_name):
        print(f"[START] Player: {player_name} (ID: {player_id})")
        db_path = 'cricket_stats.db'
        conn = create_database(db_path)
        for x in [1,2,3,6]:  # Class: 1=Test, 2=ODI, 3=T20I, 6=IPL
            is_ipl = (x == 6)
            for y in ["batting", "bowling"]:
                is_batting = (y == "batting")
                url = f"https://stats.espncricinfo.com/ci/engine/player/{player_id}.html?class={x};template=results;type={y};view=match"
                print(f"[FETCH] {player_name} ({player_id}) | {y} | {'IPL' if is_ipl else 'International'} | URL: {url}")
                max_retries = 10
                delay = 2
                for attempt in range(max_retries):
                    try:
                        scrape_and_store_tables(conn, url, player_id, player_name, class_id=x, is_ipl=is_ipl, is_batting=is_batting)
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
    