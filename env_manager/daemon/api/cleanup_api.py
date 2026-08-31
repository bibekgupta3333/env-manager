"""REST API — cleanup endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from env_manager.adapters.registry import AdapterRegistry
from env_manager.cli.db_utils import get_db_path
from env_manager.cli.resolve import resolve_env
from env_manager.models.states import ManagementState
from env_manager.platform import safe_rmtree
from env_manager.storage.database import get_connection
from env_manager.storage.repo_activity import ActivityRepository
from env_manager.storage.repo_env import EnvironmentRepository
from env_manager.storage.repo_project import ProjectRepository
from env_manager.storage.repo_snapshot import SnapshotRepository

router = APIRouter(prefix="/api/cleanup", tags=["cleanup"])


@router.post("/execute")
async def cleanup_execute(body: dict[str, Any]):
    stale_days = body.get("stale_days", 60)
    orphaned = body.get("orphaned", False)
    snapshot = body.get("snapshot", False)
    dry_run = body.get("dry_run", True)
    conn = get_connection(get_db_path())
    try:
        env_repo = EnvironmentRepository(conn)
        proj_repo = ProjectRepository(conn)
        snap_repo = SnapshotRepository(conn)
        activity_repo = ActivityRepository(conn)
        registry = AdapterRegistry(conn)
        candidates: list[dict[str, Any]] = []
        if stale_days > 0:
            stale_envs = env_repo.list_stale(days=stale_days)
            candidates.extend(dict(e) for e in stale_envs)
        if orphaned:
            orphan_envs = env_repo.list_orphaned()
            candidates.extend(dict(e) for e in orphan_envs)
        filtered = []
        for env in candidates:
            if env.get("project_id"):
                proj = proj_repo.get_by_id(env["project_id"])
                if proj and proj["is_pinned"]:
                    continue
            filtered.append(env)
        candidates = filtered

        if dry_run:
            total = sum(e.get("size_bytes", 0) or 0 for e in candidates)
            return {
                "status": "preview",
                "count": len(candidates),
                "total_bytes": total,
                "dry_run": True,
            }

        processed = 0
        freed = 0
        for env in candidates:
            snapshot_created = False
            if snapshot:
                adapter = registry.get(env["adapter"])
                if adapter:
                    try:
                        fr = adapter.freeze(Path(env["path"]))
                        snap_repo.insert(
                            env_id=env["id"],
                            frozen_deps={
                                p.name: p.version for p in fr.packages
                            },
                            raw_lockfile=fr.raw_content,
                            lockfile_format=fr.format,
                        )
                        snapshot_created = True
                    except (OSError, ValueError):
                        pass
            env_repo.update_state(
                env["id"],
                (
                    ManagementState.SNAPSHOTTED
                    if snapshot_created
                    else ManagementState.DELETED
                ),
            )
            activity_repo.log(
                event="cleaned_up",
                env_id=env["id"],
                detail={"freed_bytes": env.get("size_bytes", 0)},
            )
            env_path = Path(env["path"])
            if env_path.exists():
                safe_rmtree(env_path)
            processed += 1
            freed += env.get("size_bytes", 0) or 0
        return {
            "status": "ok",
            "processed": processed,
            "freed_bytes": freed,
            "freed_human": _fmt_size(freed),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/gc")
async def cleanup_gc(body: dict[str, Any]):
    dry_run = body.get("dry_run", True)
    conn = get_connection(get_db_path())
    try:
        env_repo = EnvironmentRepository(conn)
        deleted = env_repo.list_by_state(ManagementState.DELETED)
        snapshotted = env_repo.list_by_state(ManagementState.SNAPSHOTTED)
        all_deleted = list(deleted) + list(snapshotted)
        if dry_run:
            total = sum(e["size_bytes"] for e in all_deleted)
            return {
                "status": "preview",
                "count": len(all_deleted),
                "total_bytes": total,
                "total_human": _fmt_size(total),
                "dry_run": True,
            }
        for env in all_deleted:
            env_repo.update_state(env["id"], ManagementState.PURGED)
        return {
            "status": "ok",
            "purged": len(all_deleted),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/compare")
async def cleanup_compare(body: dict[str, Any]):
    project_a = body.get("project_a", "")
    project_b = body.get("project_b", "")
    if not project_a or not project_b:
        raise HTTPException(
            status_code=400,
            detail="project_a and project_b are required",
        )
    conn = get_connection(get_db_path())
    try:
        registry = AdapterRegistry(conn)

        def _get_packages(identifier: str):
            env = resolve_env(conn, identifier)
            if not env:
                return None, {}
            adapter = registry.get(env["adapter"])
            if not adapter:
                return env, {}
            pkgs = {
                p.name: p.version
                for p in adapter.get_packages(Path(env["path"]))
            }
            return env, pkgs

        env_a, pkgs_a = _get_packages(project_a)
        env_b, pkgs_b = _get_packages(project_b)
        if not env_a or not env_b:
            raise HTTPException(
                status_code=404,
                detail="One or both environments not found",
            )
        only_a = {k: v for k, v in pkgs_a.items() if k not in pkgs_b}
        only_b = {k: v for k, v in pkgs_b.items() if k not in pkgs_a}
        different = {
            k: {"a": pkgs_a[k], "b": pkgs_b[k]}
            for k in pkgs_a
            if k in pkgs_b and pkgs_a[k] != pkgs_b[k]
        }
        return {
            "project_a": {
                "identifier": project_a,
                "env_id": env_a["id"],
                "packages": len(pkgs_a),
            },
            "project_b": {
                "identifier": project_b,
                "env_id": env_b["id"],
                "packages": len(pkgs_b),
            },
            "only_in_a": only_a,
            "only_in_b": only_b,
            "different_versions": different,
            "identical": not only_a and not only_b and not different,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


def _fmt_size(size_bytes: int) -> str:
    if size_bytes >= 1_000_000_000:
        return f"{size_bytes / 1_000_000_000:.1f} GB"
    if size_bytes >= 1_000_000:
        return f"{size_bytes / 1_000_000:.1f} MB"
    if size_bytes >= 1_000:
        return f"{size_bytes / 1_000:.1f} KB"
    return f"{size_bytes} B"
