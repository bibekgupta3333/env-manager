"""Filesystem scanner — discovers environments using enabled adapters."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from env_manager.adapters.base import BaseAdapter
from env_manager.models.env import EnvMetadata
from env_manager.models.states import DiscoveryStatus, ManagementState
from env_manager.platform import system_excludes
from env_manager.storage.repo_activity import ActivityRepository
from env_manager.storage.repo_env import EnvironmentRepository
from env_manager.storage.repo_project import ProjectRepository

DEFAULT_EXCLUDES: set[str] = {
    "node_modules",
    ".git",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".eggs",
    "dist",
    "build",
    # IDE extension installs (not user projects)
    "extensions",
    # Package manager caches (auto-managed, not user envs)
    "pre-commit",
    "uv",
}

# System paths determined at runtime per platform
SYSTEM_PREFIXES: list[str] = system_excludes()


class Scanner:
    def __init__(self, conn: sqlite3.Connection, adapters: list[BaseAdapter]):
        self.conn = conn
        self.adapters = adapters
        self.env_repo = EnvironmentRepository(conn)
        self.proj_repo = ProjectRepository(conn)
        self.activity_repo = ActivityRepository(conn)

    def scan(
        self, root_path: str, depth: int = 5, incremental: bool = False
    ) -> list[EnvMetadata]:
        root = Path(root_path).expanduser().resolve()
        if not root.exists():
            return []

        last_scan: str | None = None
        if incremental:
            last_scan = self._get_last_scan_time()

        results: list[EnvMetadata] = []
        self._walk(root, depth, results, last_scan)

        self.activity_repo.log(
            event="scan_started",
            detail={"root": str(root), "incremental": incremental},
        )

        for meta in results:
            self._persist(meta)

        self.activity_repo.log(
            event="scan_completed",
            detail={"envs_found": len(results), "root": str(root)},
        )
        return results

    def _get_last_scan_time(self) -> str | None:
        """Get the timestamp of the most recent scan from activity_log."""
        row = self.conn.execute(
            "SELECT MAX(timestamp) FROM activity_log "
            "WHERE event = 'scan_completed'"
        ).fetchone()
        return row[0] if row and row[0] else None

    @staticmethod
    def _project_name(env_path: Path, env_type: str) -> str:
        if env_type == "local":
            parent = env_path.parent
            name = parent.name.lower()
            if name.startswith("pytest") or name.startswith("tmp"):
                name = parent.parent.name
            else:
                name = parent.name
        else:
            name = env_path.name
        return name.lstrip(".")

    def _persist(self, meta: EnvMetadata) -> None:
        """Store discovered environment in the database."""
        env_path = Path(meta.path).resolve()
        proj_dir = env_path.parent if meta.env_type == "local" else env_path
        proj_dir = proj_dir.resolve()
        proj_name = self._project_name(env_path, meta.env_type)

        # If the project directory no longer exists but the venv path
        # is already tracked under a different project, link to it
        # instead of creating a duplicate.
        if not proj_dir.exists():
            existing_env = self.env_repo.get_by_path(str(env_path))
            if existing_env:
                self.activity_repo.log(
                    event="env_linked",
                    env_id=existing_env["id"],
                    project_id=existing_env["project_id"],
                    detail={
                        "path": str(env_path),
                        "missing_project_dir": str(proj_dir),
                        "linked_to_project_id": (
                            existing_env["project_id"]
                        ),
                    },
                )
                return

        proj_id, _ = self.proj_repo.get_or_create(
            name=proj_name, path=str(proj_dir)
        )

        existing = self.conn.execute(
            "SELECT * FROM environments "
            "WHERE path = ? AND project_id = ? "
            "AND management_state != 'purged'",
            (str(env_path), proj_id),
        ).fetchone()
        if existing:
            self.env_repo.mark_scanned(existing["id"])
            self.env_repo.update_size(existing["id"], meta.size_bytes)
            self.env_repo.touch(existing["id"])
            self._detect_nested_venv(existing["id"], env_path, proj_dir)
            self._detect_shared_env(str(env_path), proj_id)
            return

        metadata: dict[str, Any] = {"interpreter_path": meta.interpreter_path}

        parent_venv_path = proj_dir.parent / ".venv"
        if parent_venv_path.exists():
            parent_env = self.env_repo.get_by_path(str(parent_venv_path))
            if parent_env:
                metadata["parent_env_id"] = parent_env["id"]

        adapter_name = f"{meta.language}.{meta.tool}"
        new_id = self.env_repo.insert(
            project_id=proj_id,
            adapter=adapter_name,
            env_type=meta.env_type,
            path=str(env_path),
            language=meta.language,
            version=meta.version,
            tool=meta.tool,
            size_bytes=meta.size_bytes,
            management_state=ManagementState.READY,
            discovery_status=DiscoveryStatus.TRACKED,
            metadata=metadata,
        )

        self.activity_repo.log(
            event="discovered",
            project_id=proj_id,
            detail={"path": str(env_path), "language": meta.language},
        )

        self._detect_nested_venv(new_id, env_path, proj_dir)
        self._detect_shared_env(str(env_path), proj_id)

    def _detect_nested_venv(
        self, env_id: int, env_path: Path, proj_dir: Path
    ) -> None:
        """Check for nested .venv: if the parent directory also has a
        .venv, record the parent env id in metadata."""
        parent_venv_path = proj_dir.parent / ".venv"
        if parent_venv_path.exists():
            parent_env = self.env_repo.get_by_path(str(parent_venv_path))
            if parent_env:
                existing = self.env_repo.get_by_id(env_id)
                if existing:
                    metadata = json.loads(existing["metadata"] or "{}")
                    metadata["parent_env_id"] = parent_env["id"]
                    self.env_repo.update_metadata(env_id, metadata)

    def _detect_shared_env(
        self, env_path: str, project_id: int
    ) -> None:
        """Check if this environment path is shared with other projects.

        When the same venv path is associated with multiple projects
        (e.g. a monorepo shared venv), updates metadata on all
        involved environments and logs a shared_env_detected activity.
        """
        rows = self.conn.execute(
            "SELECT id, project_id, metadata FROM environments "
            "WHERE path = ? AND project_id != ? "
            "AND management_state != 'purged'",
            (env_path, project_id),
        ).fetchall()

        if not rows:
            return

        other_project_ids = [row["project_id"] for row in rows]
        all_project_ids = sorted(set(other_project_ids + [project_id]))

        # Update metadata on all other environments sharing this path
        for row in rows:
            existing_meta = json.loads(row["metadata"] or "{}")
            if existing_meta.get("shared_with_project_ids") != all_project_ids:
                existing_meta["shared_with_project_ids"] = all_project_ids
                self.env_repo.update_metadata(row["id"], existing_meta)

        # Update metadata on the current environment too
        current_env = self.conn.execute(
            "SELECT id, metadata FROM environments "
            "WHERE path = ? AND project_id = ?",
            (env_path, project_id),
        ).fetchone()
        if current_env:
            current_meta = json.loads(current_env["metadata"] or "{}")
            if current_meta.get("shared_with_project_ids") != all_project_ids:
                current_meta["shared_with_project_ids"] = all_project_ids
                self.env_repo.update_metadata(
                    current_env["id"], current_meta
                )

        self.activity_repo.log(
            event="shared_env_detected",
            project_id=project_id,
            detail={
                "path": env_path,
                "shared_with_project_ids": other_project_ids,
            },
        )

    def _walk(
        self,
        directory: Path,
        remaining_depth: int,
        results: list[EnvMetadata],
        last_scan: str | None = None,
    ) -> None:
        if remaining_depth <= 0:
            return

        if directory.name in DEFAULT_EXCLUDES:
            return

        path_str = str(directory)
        if any(path_str.startswith(p) for p in SYSTEM_PREFIXES):
            return

        # Incremental: skip directories older than last scan
        if last_scan:
            try:
                dir_mtime = directory.stat().st_mtime

                scan_dt = datetime.fromisoformat(last_scan)
                if dir_mtime < scan_dt.timestamp():
                    return
            except (OSError, ValueError):
                pass

        for adapter in self.adapters:
            try:
                meta = adapter.detect(directory)
                if meta is not None:
                    results.append(meta)
                    break
            except OSError:
                continue

        try:
            for entry in directory.iterdir():
                if entry.is_dir() and not entry.is_symlink():
                    self._walk(entry, remaining_depth - 1, results)
        except PermissionError:
            pass
