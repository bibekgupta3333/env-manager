"""Repository for snapshot CRUD operations."""

# mypy: disable_error_code = no-any-return

from __future__ import annotations

import json
import sqlite3
from typing import Any


class SnapshotRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def insert(self, env_id: int, frozen_deps: dict[str, Any], raw_lockfile: str = "",
               lockfile_format: str = "", tool_config: dict[str, Any] | None = None,
               notes: str = "") -> tuple[int, int]:
        latest = self.get_latest_version(env_id)
        version = (latest or 0) + 1
        cursor = self.conn.execute(
            """INSERT INTO snapshots (env_id, version, frozen_deps, raw_lockfile,
               lockfile_format, tool_config, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (env_id, version, json.dumps(frozen_deps), raw_lockfile,
             lockfile_format, json.dumps(tool_config or {}), notes),
        )
        self.conn.commit()
        assert cursor.lastrowid is not None
        return cursor.lastrowid, version

    def get_latest_version(self, env_id: int) -> int | None:
        row = self.conn.execute(
            "SELECT MAX(version) FROM snapshots WHERE env_id = ?", (env_id,)
        ).fetchone()
        return row[0] if row else None

    def get_by_env_and_version(self, env_id: int, version: int) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM snapshots WHERE env_id = ? AND version = ?",
            (env_id, version),
        ).fetchone()

    def get_latest(self, env_id: int) -> sqlite3.Row | None:
        version = self.get_latest_version(env_id)
        if version is None:
            return None
        return self.get_by_env_and_version(env_id, version)

    def list_by_env(self, env_id: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM snapshots WHERE env_id = ? ORDER BY version DESC",
            (env_id,),
        ).fetchall()

    def list_all(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            """SELECT s.*, e.language, e.version as env_version, e.tool
               FROM snapshots s
               JOIN environments e ON s.env_id = e.id
               ORDER BY s.created_at DESC"""
        ).fetchall()

    def prune(self, env_id: int, keep: int = 5) -> int:
        versions = self.conn.execute(
            "SELECT version FROM snapshots WHERE env_id = ? ORDER BY version DESC",
            (env_id,),
        ).fetchall()
        if len(versions) <= keep:
            return 0
        to_delete = [v[0] for v in versions[keep:]]
        self.conn.executemany(
            "DELETE FROM snapshots WHERE env_id = ? AND version = ?",
            [(env_id, v) for v in to_delete],
        )
        self.conn.commit()
        return len(to_delete)
