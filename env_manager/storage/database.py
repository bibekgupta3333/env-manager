"""SQLite database connection management."""

import atexit
import contextlib
import shutil
import sqlite3
from pathlib import Path
from threading import Lock

from env_manager.exceptions import StorageError

_connections: dict[str, sqlite3.Connection] = {}
_refcounts: dict[str, int] = {}
_lock = Lock()
_MAX_CONNECTIONS = 64

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

    version = conn.execute(
        "SELECT MAX(version) FROM _schema_version"
    ).fetchone()[0]

    if version is None or version < 1:
        conn.execute(
            "UPDATE environments SET env_type = 'runtime' "
            "WHERE env_type = 'global'"
        )
        conn.execute(
            "UPDATE environments SET env_type = 'project' "
            "WHERE env_type = 'local'"
        )
        conn.commit()

        try:
            conn.execute(
                "DELETE FROM environments WHERE rowid NOT IN "
                "(SELECT MIN(rowid) FROM environments "
                "WHERE management_state != 'purged' GROUP BY path)"
            )
            conn.execute("DROP INDEX IF EXISTS idx_envs_path")
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_envs_path_unique "
                "ON environments(path)"
            )
        except sqlite3.OperationalError:
            pass

        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS trg_projects_delete_cascade
            BEFORE DELETE ON projects
            FOR EACH ROW
            BEGIN
                DELETE FROM environments WHERE project_id = OLD.id;
            END
        """
        )
        conn.commit()

        conn.execute("INSERT INTO _schema_version (version) VALUES (1)")
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
        return False  # Cannot determine disk space


def get_connection(db_path: str) -> sqlite3.Connection:
    """Get or create a connection for the given DB path. Thread-safe."""
    with _lock:
        if len(_connections) >= _MAX_CONNECTIONS:
            oldest = next(iter(_connections))
            _connections[oldest].close()
            del _connections[oldest]
            _refcounts.pop(oldest, None)
        existing = _connections.get(db_path)
        if existing is not None:
            try:
                existing.execute("SELECT 1")
                _refcounts[db_path] = _refcounts.get(db_path, 0) + 1
                return existing
            except sqlite3.ProgrammingError:
                del _connections[db_path]
                _refcounts.pop(db_path, None)
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _connections[db_path] = conn
        _refcounts[db_path] = 1
        return conn


def close_connection(db_path: str) -> None:
    """Close and remove a connection when all callers have released it."""
    with _lock:
        refcount = _refcounts.get(db_path, 0)
        if refcount <= 1:
            _refcounts.pop(db_path, None)
            conn = _connections.pop(db_path, None)
            if conn:
                conn.close()
        else:
            _refcounts[db_path] = refcount - 1


@atexit.register
def _close_all_connections() -> None:
    with _lock:
        for _, conn in list(_connections.items()):
            with contextlib.suppress(Exception):
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            with contextlib.suppress(Exception):
                conn.close()
        _connections.clear()
        _refcounts.clear()
