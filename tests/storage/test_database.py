"""Tests for SQLite database layer."""

import sqlite3

from env_manager.storage.database import (
    close_connection,
    get_connection,
    init_db,
)


def test_init_db_creates_all_tables(db_path):
    init_db(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in cursor.fetchall()]

    assert "projects" in tables
    assert "environments" in tables
    assert "snapshots" in tables
    assert "packages" in tables
    assert "activity_log" in tables
    assert "scan_history" in tables
    assert "cleanup_rules" in tables
    assert "adapter_registry" in tables
    conn.close()
    close_connection(db_path)


def test_wal_mode_enabled(db_path):
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("PRAGMA journal_mode")
    assert cursor.fetchone()[0].lower() == "wal"
    conn.close()
    close_connection(db_path)


def test_get_connection_returns_same_instance(db_path):
    init_db(db_path)
    conn1 = get_connection(db_path)
    conn2 = get_connection(db_path)
    assert conn1 is conn2
    conn1.close()
    close_connection(db_path)


def test_foreign_keys_enabled(db_path):
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.execute("PRAGMA foreign_keys")
    assert cursor.fetchone()[0] == 1
    conn.close()
    close_connection(db_path)


def test_init_db_is_idempotent(db_path):
    init_db(db_path)
    init_db(db_path)  # Second call should not raise
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in cursor.fetchall()]
    assert "environments" in tables
    conn.close()
    close_connection(db_path)
