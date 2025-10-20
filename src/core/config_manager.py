import json
from database import get_connection, init_db
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "../data/config.json")

def save_config(config_dict):
    """Save config to JSON and SQLite"""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config_dict, f, indent=4)

    conn = get_connection()
    cursor = conn.cursor()
    for key, value in config_dict.items():
        cursor.execute("REPLACE INTO config (key, value) VALUES (?, ?)", (key, json.dumps(value)))
    conn.commit()
    conn.close()

def load_config():
    """Load config from SQLite, fallback to JSON"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM config")
    rows = cursor.fetchall()
    conn.close()

    if rows:
        return {key: json.loads(value) for key, value in rows}

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)

    return {}