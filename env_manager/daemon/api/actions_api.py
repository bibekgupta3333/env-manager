"""REST API — environment action endpoints."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from env_manager.adapters.registry import AdapterRegistry
from env_manager.cli.db_utils import get_db_path
from env_manager.models.states import ManagementState
from env_manager.platform import safe_rmtree
from env_manager.storage.database import get_connection
from env_manager.storage.repo_env import EnvironmentRepository
from env_manager.storage.repo_project import ProjectRepository
from env_manager.storage.repo_snapshot import SnapshotRepository

router = APIRouter(prefix="/api/envs", tags=["environment-actions"])


@router.post("/{env_id}/install")
async def install_packages(env_id: int, body: dict[str, Any]):
    packages = body.get("packages", [])
    if not packages:
        raise HTTPException(
            status_code=400, detail="packages list is required"
        )
    conn = get_connection(get_db_path())
    try:
        env_repo = EnvironmentRepository(conn)
        env = env_repo.get_by_id(env_id)
        if not env:
            raise HTTPException(
                status_code=404, detail="Environment not found"
            )
        registry = AdapterRegistry(conn)
        adapter = registry.get(env["adapter"])
        if not adapter:
            msg = f"Adapter not found: {env['adapter']}"
            raise HTTPException(status_code=400, detail=msg)
        adapter.install(Path(env["path"]), list(packages))
        return {"status": "ok", "env_id": env_id, "installed": len(packages)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/{env_id}/uninstall")
async def uninstall_packages(env_id: int, body: dict[str, Any]):
    packages = body.get("packages", [])
    if not packages:
        raise HTTPException(
            status_code=400, detail="packages list is required"
        )
    conn = get_connection(get_db_path())
    try:
        env_repo = EnvironmentRepository(conn)
        env = env_repo.get_by_id(env_id)
        if not env:
            raise HTTPException(
                status_code=404, detail="Environment not found"
            )
        registry = AdapterRegistry(conn)
        adapter = registry.get(env["adapter"])
        if not adapter:
            msg = f"Adapter not found: {env['adapter']}"
            raise HTTPException(status_code=400, detail=msg)
        adapter.uninstall(Path(env["path"]), list(packages))
        return {"status": "ok", "env_id": env_id, "uninstalled": len(packages)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/{env_id}/pin")
async def pin_env(env_id: int):
    conn = get_connection(get_db_path())
    try:
        env_repo = EnvironmentRepository(conn)
        env = env_repo.get_by_id(env_id)
        if not env:
            raise HTTPException(
                status_code=404, detail="Environment not found"
            )
        proj_id = env["project_id"]
        if not proj_id:
            raise HTTPException(
                status_code=400,
                detail="Environment has no project",
            )
        proj_repo = ProjectRepository(conn)
        proj_repo.set_pinned(proj_id, True)
        return {"status": "pinned", "project_id": proj_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/{env_id}/unpin")
async def unpin_env(env_id: int):
    conn = get_connection(get_db_path())
    try:
        env_repo = EnvironmentRepository(conn)
        env = env_repo.get_by_id(env_id)
        if not env:
            raise HTTPException(
                status_code=404, detail="Environment not found"
            )
        proj_id = env["project_id"]
        if not proj_id:
            raise HTTPException(
                status_code=400,
                detail="Environment has no project",
            )
        proj_repo = ProjectRepository(conn)
        proj_repo.set_pinned(proj_id, False)
        return {"status": "unpinned", "project_id": proj_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/{env_id}/remove")
async def remove_env(env_id: int, body: dict[str, Any]):
    snapshot = body.get("snapshot", False)
    conn = get_connection(get_db_path())
    try:
        env_repo = EnvironmentRepository(conn)
        env = env_repo.get_by_id(env_id)
        if not env:
            raise HTTPException(
                status_code=404, detail="Environment not found"
            )
        snapshot_created = False
        if snapshot:
            registry = AdapterRegistry(conn)
            adapter = registry.get(env["adapter"])
            if adapter:
                try:
                    fr = adapter.freeze(Path(env["path"]))
                    SnapshotRepository(conn).insert(
                        env_id=env["id"],
                        frozen_deps={p.name: p.version for p in fr.packages},
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
        env_path = Path(env["path"])
        if env_path.exists():
            safe_rmtree(env_path)
        return {
            "status": "removed",
            "env_id": env_id,
            "snapshot": snapshot,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/{env_id}/restore")
async def restore_env(env_id: int, body: dict[str, Any]):
    snapshot_version = body.get("snapshot_version")
    conn = get_connection(get_db_path())
    try:
        snap_repo = SnapshotRepository(conn)
        env_repo = EnvironmentRepository(conn)
        if snapshot_version:
            snap = snap_repo.get_by_env_and_version(env_id, snapshot_version)
        else:
            snap = snap_repo.get_latest(env_id)
        if not snap:
            raise HTTPException(status_code=404, detail="No snapshot found")
        env = env_repo.get_by_id(env_id)
        if not env:
            raise HTTPException(
                status_code=404,
                detail="Original env record not found",
            )
        registry = AdapterRegistry(conn)
        adapter = registry.get(env["adapter"])
        if not adapter:
            msg = f"Adapter not found: {env['adapter']}"
            raise HTTPException(status_code=400, detail=msg)
        deps = json.loads(snap["frozen_deps"])
        adapter.create(Path(env["path"]), {"version": env["version"]})
        adapter.install(Path(env["path"]), list(deps.keys()))
        env_repo.update_state(env["id"], ManagementState.READY)
        return {
            "status": "restored",
            "env_id": env_id,
            "packages": len(deps),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
