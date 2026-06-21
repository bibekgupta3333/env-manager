"""Repository for environment CRUD operations."""

# mypy: disable_error_code = no-any-return

import json
import sqlite3
from typing import Any

from env_manager.models.states import DiscoveryStatus, ManagementState


class EnvironmentRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def insert(
        self,
        project_id: int,
        adapter: str,
        env_type: str,
        path: str,
        language: str,
        version: str,
        tool: str = "",
        size_bytes: int = 0,
        management_state: ManagementState = ManagementState.READY,
        discovery_status: DiscoveryStatus = DiscoveryStatus.UNTRACKED,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        cursor = self.conn.execute(
            """INSERT INTO environments
               (project_id, adapter, env_type, path, language, version, tool,
                size_bytes, management_state, discovery_status, metadata, last_scanned_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
            (
                project_id, adapter, env_type, path, language, version, tool,
                size_bytes, management_state.value, discovery_status.value,
                json.dumps(metadata or {}),
            ),
        )
        self.conn.commit()
        assert cursor.lastrowid is not None
        return cursor.lastrowid

    def get_by_id(self, env_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM environments WHERE id = ?", (env_id,)
        ).fetchone()

    def get_by_path(self, path: str) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM environments WHERE path = ?", (path,)
        ).fetchone()

    def list_all(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            """SELECT * FROM environments
               WHERE management_state != 'purged'
               ORDER BY language, project_id"""
        ).fetchall()

    def list_by_language(self, language: str) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM environments WHERE language = ? AND management_state != 'purged'",
            (language,),
        ).fetchall()

    def list_by_project(self, project_id: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM environments WHERE project_id = ? AND management_state != 'purged'",
            (project_id,),
        ).fetchall()

    def list_by_state(self, state: ManagementState) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM environments WHERE management_state = ?", (state.value,)
        ).fetchall()

    def list_stale(self, days: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            """SELECT * FROM environments
               WHERE management_state = 'ready'
               AND last_used_at < datetime('now', ?)""",
            (f"-{days} days",),
        ).fetchall()

    def list_orphaned(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM environments WHERE is_orphaned = 1 AND management_state != 'purged'"
        ).fetchall()

    def list_by_discovery(self, status: DiscoveryStatus) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM environments WHERE discovery_status = ?", (status.value,)
        ).fetchall()

    def update_state(self, env_id: int, state: ManagementState) -> None:
        self.conn.execute(
            "UPDATE environments SET management_state = ? WHERE id = ?",
            (state.value, env_id),
        )
        self.conn.commit()

    def update_discovery_status(self, env_id: int, status: DiscoveryStatus) -> None:
        self.conn.execute(
            "UPDATE environments SET discovery_status = ? WHERE id = ?",
            (status.value, env_id),
        )
        self.conn.commit()

    def update_size(self, env_id: int, size_bytes: int) -> None:
        self.conn.execute(
            "UPDATE environments SET size_bytes = ? WHERE id = ?",
            (size_bytes, env_id),
        )
        self.conn.commit()

    def touch(self, env_id: int) -> None:
        self.conn.execute(
            "UPDATE environments SET last_used_at = datetime('now') WHERE id = ?",
            (env_id,),
        )
        self.conn.commit()

    def mark_scanned(self, env_id: int) -> None:
        self.conn.execute(
            "UPDATE environments SET last_scanned_at = datetime('now') WHERE id = ?",
            (env_id,),
        )
        self.conn.commit()

    def update_health(self, env_id: int, result: str) -> None:
        self.conn.execute(
            """UPDATE environments
               SET last_health_check = datetime('now'), last_health_result = ?
               WHERE id = ?""",
            (result, env_id),
        )
        self.conn.commit()

    def set_orphaned(self, env_id: int, orphaned: bool) -> None:
        self.conn.execute(
            "UPDATE environments SET is_orphaned = ? WHERE id = ?",
            (int(orphaned), env_id),
        )
        self.conn.commit()

    def delete(self, env_id: int) -> None:
        self.conn.execute("DELETE FROM environments WHERE id = ?", (env_id,))
        self.conn.commit()
