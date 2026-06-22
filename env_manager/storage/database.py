"""SQLite database connection management."""

import shutil
import sqlite3
from pathlib import Path
from threading import Lock

from env_manager.exceptions import StorageError

_connections: dict[str, sqlite3.Connection] = {}
_lock = Lock()

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def init_db(db_path: str) -> None:
    """Initialize database with schema. Idempotent (IF NOT EXISTS)."""
    if not check_disk_space(db_path):
        raise StorageError(
            "insufficient disk space to initialize database; "
            "free up disk space and try again"
        )
    schema = SCHEMA_PATH.read_text()
    conn = get_connection(db_path)
    conn.executescript(schema)
    conn.commit()


def check_disk_space(db_path: str, min_bytes: int = 10_000_000) -> bool:
    """Check available disk space on the volume where db_path lives.

    Returns True if space >= min_bytes, False otherwise.
    """
    try:
        usage = shutil.disk_usage(db_path)
        return usage.free >= min_bytes
    except (FileNotFoundError, OSError):
        # Path doesn't exist yet — check the parent directory.
        parent = Path(db_path).parent
        if parent.exists():
            usage = shutil.disk_usage(parent)
            return usage.free >= min_bytes
        return True


def get_connection(db_path: str) -> sqlite3.Connection:
    """Get or create a connection for the given DB path. Thread-safe."""
    with _lock:
        if db_path not in _connections:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            _connections[db_path] = conn
        return _connections[db_path]


def close_connection(db_path: str) -> None:
    """Close and remove a connection."""
    with _lock:
        conn = _connections.pop(db_path, None)
        if conn:
            conn.close()
