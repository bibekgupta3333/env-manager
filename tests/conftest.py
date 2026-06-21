"""Test fixtures shared across all tests."""

import sqlite3

import pytest

from env_manager.storage.database import close_connection, init_db


@pytest.fixture
def db_path(tmp_path):
    """Temp SQLite database path."""
    return str(tmp_path / "test.db")


@pytest.fixture
def db_connection(db_path):
    """Initialized database connection."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()
    close_connection(db_path)


@pytest.fixture
def temp_dir(tmp_path):
    """Temporary directory for file operations."""
    return tmp_path


@pytest.fixture
def fake_venv(tmp_path):
    """Create a fake Python venv directory structure for adapter testing."""
    venv_dir = tmp_path / ".venv"
    venv_dir.mkdir()
    (venv_dir / "pyvenv.cfg").write_text(
        "home = /usr/bin\n"
        "version = 3.12.1\n"
        "include-system-site-packages = false\n"
    )
    bin_dir = venv_dir / "bin"
    bin_dir.mkdir()
    (bin_dir / "python").touch(mode=0o755)
    (bin_dir / "pip").touch(mode=0o755)
    return venv_dir
