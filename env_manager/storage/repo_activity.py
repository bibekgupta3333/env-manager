"""Repository for activity log operations."""

from __future__ import annotations

import json
import sqlite3
from typing import Any


class ActivityRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def log(
        self,
        event: str,
        env_id: int | None = None,
        project_id: int | None = None,
        detail: dict[str, Any] | None = None,
    ) -> int:
        cursor = self.conn.execute(
            "INSERT INTO activity_log "
            "(env_id, project_id, event, detail) "
            "VALUES (?, ?, ?, ?)",
            (env_id, project_id, event, json.dumps(detail or {})),
        )
        self.conn.commit()
        assert cursor.lastrowid is not None
        return cursor.lastrowid

    def list_recent(self, limit: int = 50) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()

    def list_by_env(self, env_id: int, limit: int = 50) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM activity_log "
            "WHERE env_id = ? "
            "ORDER BY timestamp DESC LIMIT ?",
            (env_id, limit),
        ).fetchall()
