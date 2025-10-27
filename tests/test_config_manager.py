import os
import sys
import json
import sqlite3
from pathlib import Path
import pytest

# Ensure we can import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.core import config_manager, database


def test_init_db_creates_tables(tmp_path, monkeypatch):
    """Test that init_db creates a SQLite database and config table."""
    # Define a temporary database path
    test_db_path = tmp_path / "test_config.db"

    # Make sure the folder exists
    test_db_path.parent.mkdir(parents=True, exist_ok=True)

    # ✅ Monkeypatch the database path constant
    monkeypatch.setattr(database, "DB_PATH", str(test_db_path))

    # Call init_db
    database.init_db()

    # ✅ Check if DB file is created
    assert test_db_path.exists(), f"Database not created at {test_db_path}"

    # ✅ Check if config table exists
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='config';")
    result = cursor.fetchone()
    conn.close()

    assert result is not None, "Config table not found in test database"


def test_save_and_load_config(tmp_path, monkeypatch):
    """Test saving and loading config to both JSON and SQLite."""
    # Temporary test file paths
    test_json = tmp_path / "test_config.json"
    test_db = tmp_path / "test_config.db"

    test_json.parent.mkdir(parents=True, exist_ok=True)
    test_db.parent.mkdir(parents=True, exist_ok=True)

    # ✅ Monkeypatch the constants used in config_manager and database
    monkeypatch.setattr(config_manager, "CONFIG_FILE", str(test_json))
    monkeypatch.setattr(database, "DB_PATH", str(test_db))

    # Initialize DB
    database.init_db()

    # Data to test
    data = {"theme": "dark", "notifications": True}

    # Save + load
    config_manager.save_config(data)
    loaded = config_manager.load_config()

    # ✅ Check that loaded config matches
    assert loaded == data, f"Loaded config {loaded} != expected {data}"

    # ✅ Check JSON file exists
    assert test_json.exists(), "Config JSON file was not created"

    # ✅ Verify the data in the database
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM config")
    rows = cursor.fetchall()
    conn.close()

    db_data = {k: json.loads(v) for k, v in rows}
    assert db_data == data, f"Database contents {db_data} != expected {data}"
