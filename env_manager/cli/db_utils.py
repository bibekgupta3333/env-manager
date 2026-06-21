"""Shared CLI utilities — DB path and helpers."""

import os
from pathlib import Path

DEFAULT_DB_PATH = os.path.expanduser("~/.env-manager/envs.db")


def get_db_path() -> str:
    return os.environ.get("ENVS_DB_PATH", DEFAULT_DB_PATH)


def ensure_db_dir() -> None:
    db_dir = Path(get_db_path()).parent
    db_dir.mkdir(parents=True, exist_ok=True)
