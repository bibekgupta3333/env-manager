"""Repository for project CRUD operations."""

# mypy: disable_error_code = no-any-return

import json
import sqlite3


class ProjectRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def insert(self, name: str, path: str, tags: list[str] | None = None) -> int:
        cursor = self.conn.execute(
            "INSERT INTO projects (name, path, tags) VALUES (?, ?, ?)",
            (name, path, json.dumps(tags or [])),
        )
        self.conn.commit()
        assert cursor.lastrowid is not None
        return cursor.lastrowid

    def get_by_id(self, project_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()

    def get_by_path(self, path: str) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM projects WHERE path = ?", (path,)
        ).fetchone()

    def get_or_create(self, name: str, path: str) -> tuple[int, bool]:
        existing = self.get_by_path(path)
        if existing:
            return existing["id"], False
        return self.insert(name=name, path=path), True

    def list_all(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM projects ORDER BY name"
        ).fetchall()

    def set_pinned(self, project_id: int, pinned: bool) -> None:
        self.conn.execute(
            "UPDATE projects SET is_pinned = ?, updated_at = datetime('now') WHERE id = ?",
            (int(pinned), project_id),
        )
        self.conn.commit()

    def touch(self, project_id: int) -> None:
        self.conn.execute(
            """UPDATE projects
               SET last_active = datetime('now'), updated_at = datetime('now')
               WHERE id = ?""",
            (project_id,),
        )
        self.conn.commit()
