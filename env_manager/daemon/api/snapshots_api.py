"""REST API — snapshot endpoints."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from env_manager.adapters.registry import AdapterRegistry
from env_manager.cli.db_utils import get_db_path
from env_manager.models.states import ManagementState
from env_manager.storage.database import get_connection
from env_manager.storage.repo_env import EnvironmentRepository
from env_manager.storage.repo_snapshot import SnapshotRepository

router = APIRouter(prefix="/api/snapshots", tags=["snapshots"])


@router.get("/")
async def list_snapshots():
    conn = get_connection(get_db_path())
    repo = SnapshotRepository(conn)
    snapshots = repo.list_all()
    return {"snapshots": [dict(s) for s in snapshots], "count": len(snapshots)}


@router.get("/{snapshot_id}")
async def get_snapshot(snapshot_id: int):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/{snapshot_id}/restore")
async def restore_snapshot(snapshot_id: int):
    conn = get_connection(get_db_path())
    try:
        snap_repo = SnapshotRepository(conn)
        snap_rows = [s for s in snap_repo.list_all() if s["id"] == snapshot_id]
        if not snap_rows:
            raise HTTPException(status_code=404, detail="Snapshot not found")
        snap = snap_rows[0]
        env_repo = EnvironmentRepository(conn)
        env = env_repo.get_by_id(snap["env_id"])
        if not env:
            raise HTTPException(
                status_code=404, detail="Original env not found"
            )
        registry = AdapterRegistry(conn)
        adapter = registry.get(env["adapter"])
        if not adapter:
            msg = f"No adapter: {env['adapter']}"
            raise HTTPException(status_code=400, detail=msg)
        deps = json.loads(snap["frozen_deps"])
        adapter.create(Path(env["path"]), {"version": env["version"]})
        adapter.install(Path(env["path"]), list(deps.keys()))
        env_repo.update_state(env["id"], ManagementState.READY)
        return {
            "status": "restored",
            "snapshot_id": snapshot_id,
            "env_id": env["id"],
            "packages": len(deps),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/prune")
async def prune_snapshots(body: dict[str, Any]):
    keep = body.get("keep", 5)
    conn = get_connection(get_db_path())
    try:
        snap_repo = SnapshotRepository(conn)
        env_repo = EnvironmentRepository(conn)
        envs = env_repo.list_all()
        env_ids = [e["id"] for e in envs]
        total_pruned = 0
        for eid in env_ids:
            pruned = snap_repo.prune(eid, keep=keep)
            total_pruned += pruned
        return {
            "status": "ok",
            "pruned": total_pruned,
            "keep": keep,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
