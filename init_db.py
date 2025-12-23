#!/usr/bin/env python3
"""Initialize the stations database with NOVA channel IDs."""
import sqlite3

NOVA_CHANNELS = [
    {"channel_id": "6263", "name": "Nova Sport 1"},
    {"channel_id": "7401", "name": "Nova Sport 2"},
    {"channel_id": "7747", "name": "Nova Sport 3"},
    {"channel_id": "7612", "name": "Nova Sport 4"},
    {"channel_id": "392147", "name": "Nova Sport 5"},
    {"channel_id": "392164", "name": "Nova Sport 6"},
]


def init_db(db_path: str = "stations.sqlite.db"):
    """Create and populate the channels table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT NOT NULL UNIQUE,
            name TEXT
        )
    """)
    
    for channel in NOVA_CHANNELS:
        cursor.execute(
            "INSERT OR IGNORE INTO channels (channel_id, name) VALUES (?, ?)",
            (channel["channel_id"], channel["name"])
        )
    
    conn.commit()
    
    # Show what's in the database
    cursor.execute("SELECT * FROM channels")
    print("Channels in database:")
    for row in cursor.fetchall():
        print(f"  {row}")
    
    conn.close()


if __name__ == "__main__":
    init_db()

