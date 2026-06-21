"""Filesystem scanner — discovers environments using enabled adapters."""

import sqlite3
from pathlib import Path

from env_manager.adapters.base import BaseAdapter
from env_manager.models.env import EnvMetadata
from env_manager.models.states import DiscoveryStatus, ManagementState
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
}

SYSTEM_PREFIXES: list[str] = [
    "/usr",
    "/System",
    "/Library",
    "/proc",
    "/sys",
    "/dev",
]


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

        # Get last scan time for incremental mode
        last_scan: str | None = None
        if incremental:
            last_scan = self._get_last_scan_time()

        results: list[EnvMetadata] = []
        self._walk(root, depth, results, last_scan)

        # Record this scan
        self.activity_repo.log(
            event="scan_started",
            detail={"root": str(root), "incremental": incremental},
        )

        # Persist to database
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

    def _persist(self, meta: EnvMetadata) -> None:
        """Store discovered environment in the database."""
        env_path = Path(meta.path).resolve()
        proj_dir = env_path.parent if meta.env_type == "local" else env_path
        proj_dir = proj_dir.resolve()
        proj_name = proj_dir.name

        # Create or get project
        proj_id, _ = self.proj_repo.get_or_create(
            name=proj_name, path=str(proj_dir)
        )

        # Check if env already exists
        existing = self.env_repo.get_by_path(str(env_path))
        if existing:
            self.env_repo.mark_scanned(existing["id"])
            self.env_repo.update_size(existing["id"], meta.size_bytes)
            self.env_repo.touch(existing["id"])
            return

        # Insert new environment
        adapter_name = f"{meta.language}.{meta.tool}"
        self.env_repo.insert(
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
            metadata={"interpreter_path": meta.interpreter_path},
        )

        self.activity_repo.log(
            event="discovered",
            project_id=proj_id,
            detail={"path": str(env_path), "language": meta.language},
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
                from datetime import datetime

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
            except Exception:
                continue

        try:
            for entry in directory.iterdir():
                if entry.is_dir() and not entry.is_symlink():
                    self._walk(entry, remaining_depth - 1, results)
        except PermissionError:
            pass
