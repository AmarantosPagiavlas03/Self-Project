import sqlite3

# Initialize database
def init_db():
    conn = sqlite3.connect("soccer.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            position TEXT,
            agility INTEGER,
            power INTEGER,
            speed INTEGER
        )
    """)
    conn.commit()
    conn.close()

# Add a player
def add_player(first_name, last_name, position, agility, power, speed):
    conn = sqlite3.connect("soccer.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO players (first_name, last_name, position, agility, power, speed)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (first_name, last_name, position, agility, power, speed))
    conn.commit()
    conn.close()

# Search players based on filters
def search_players(position=None, min_agility=0, min_power=0, min_speed=0):
    conn = sqlite3.connect("soccer.db")
    cursor = conn.cursor()
    query = "SELECT * FROM players WHERE agility >= ? AND power >= ? AND speed >= ?"
    params = [min_agility, min_power, min_speed]

    if position:
        query += " AND position = ?"
        params.append(position)

    cursor.execute(query, params)
    players = cursor.fetchall()
    conn.close()
    return players
