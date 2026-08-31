"""REST API — track/ignore endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from env_manager.adapters.registry import AdapterRegistry
from env_manager.cli.db_utils import get_db_path
from env_manager.models.states import DiscoveryStatus
from env_manager.storage.database import get_connection
from env_manager.storage.repo_env import EnvironmentRepository
from env_manager.storage.repo_project import ProjectRepository

router = APIRouter(prefix="/api", tags=["track"])


@router.post("/track")
async def track_path(body: dict[str, Any]):
    path = body.get("path", "")
    if not path:
        raise HTTPException(status_code=400, detail="path is required")
    conn = get_connection(get_db_path())
    try:
        env_repo = EnvironmentRepository(conn)
        proj_repo = ProjectRepository(conn)
        registry = AdapterRegistry(conn)
        resolved = str(Path(path).resolve())
        existing = env_repo.get_by_path(resolved)
        if existing:
            env_repo.update_discovery_status(
                existing["id"], DiscoveryStatus.TRACKED
            )
            return {
                "status": "tracked",
                "path": resolved,
                "env_id": existing["id"],
            }
        adapters = registry.get_all_enabled()
        for adapter in adapters:
            meta = adapter.detect(Path(resolved))
            if meta:
                proj_dir = (
                    Path(resolved).parent
                    if adapter.env_type == "project"
                    else Path(resolved)
                )
                proj_id, _ = proj_repo.get_or_create(
                    name=proj_dir.name, path=str(proj_dir.resolve())
                )
                new_id = env_repo.insert(
                    project_id=proj_id,
                    adapter=adapter.name,
                    env_type=adapter.env_type,
                    path=resolved,
                    language=meta.language,
                    version=meta.version,
                    tool=meta.tool,
                    size_bytes=meta.size_bytes,
                    discovery_status=DiscoveryStatus.TRACKED,
                )
                return {
                    "status": "tracked",
                    "path": resolved,
                    "env_id": new_id,
                    "adapter": adapter.name,
                }
        raise HTTPException(
            status_code=400,
            detail=f"could not detect environment at: {resolved}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/ignore")
async def ignore_path(body: dict[str, Any]):
    path = body.get("path", "")
    if not path:
        raise HTTPException(status_code=400, detail="path is required")
    conn = get_connection(get_db_path())
    try:
        env_repo = EnvironmentRepository(conn)
        resolved = str(Path(path).resolve())
        existing = env_repo.get_by_path(resolved)
        if existing:
            env_repo.update_discovery_status(
                existing["id"], DiscoveryStatus.IGNORED
            )
            return {
                "status": "ignored",
                "path": resolved,
                "env_id": existing["id"],
            }
        return {
            "status": "ignored",
            "path": resolved,
            "note": "path not tracked",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
