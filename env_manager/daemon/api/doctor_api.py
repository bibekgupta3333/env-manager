"""REST API — doctor/health endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from env_manager.adapters.registry import AdapterRegistry
from env_manager.cli.db_utils import get_db_path
from env_manager.storage.database import get_connection
from env_manager.storage.repo_env import EnvironmentRepository
from env_manager.storage.repo_project import ProjectRepository
from env_manager.storage.repo_snapshot import SnapshotRepository

router = APIRouter(prefix="/api/doctor", tags=["doctor"])

_NON_ACTIVE = ("purged", "snapshotted", "deleted")


@router.post("/run")
async def doctor_run():
    conn = get_connection(get_db_path())
    try:
        env_repo = EnvironmentRepository(conn)
        proj_repo = ProjectRepository(conn)
        registry = AdapterRegistry(conn)
        envs = env_repo.list_all()
        envs = [e for e in envs if e["management_state"] not in _NON_ACTIVE]
        results = []
        for env in envs:
            proj = (
                proj_repo.get_by_id(env["project_id"])
                if env["project_id"]
                else None
            )
            proj_name = proj["name"] if proj else env["path"]
            adapter = registry.get(env["adapter"])
            if not adapter:
                results.append(
                    {
                        "env_id": env["id"],
                        "project_name": proj_name,
                        "language": env["language"],
                        "version": env["version"],
                        "status": "unknown",
                        "errors": [f"No adapter found for {env['adapter']}"],
                    }
                )
                continue
            health = adapter.check_health(Path(env["path"]))
            env_repo.update_health(env["id"], health.status)
            results.append(
                {
                    "env_id": env["id"],
                    "project_name": proj_name,
                    "language": env["language"],
                    "version": env["version"],
                    "status": health.status,
                    "errors": health.errors,
                    "suggestions": health.suggestions,
                }
            )
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/fix")
async def doctor_fix():
    conn = get_connection(get_db_path())
    try:
        env_repo = EnvironmentRepository(conn)
        proj_repo = ProjectRepository(conn)
        registry = AdapterRegistry(conn)
        snap_repo = SnapshotRepository(conn)
        envs = env_repo.list_all()
        envs = [e for e in envs if e["management_state"] not in _NON_ACTIVE]
        results = []
        for env in envs:
            proj = (
                proj_repo.get_by_id(env["project_id"])
                if env["project_id"]
                else None
            )
            proj_name = proj["name"] if proj else env["path"]
            adapter = registry.get(env["adapter"])
            if not adapter:
                results.append(
                    {
                        "env_id": env["id"],
                        "project_name": proj_name,
                        "language": env["language"],
                        "version": env["version"],
                        "status": "unknown",
                        "errors": [f"No adapter found for {env['adapter']}"],
                    }
                )
                continue
            health = adapter.check_health(Path(env["path"]))
            env_repo.update_health(env["id"], health.status)
            result = {
                "env_id": env["id"],
                "project_name": proj_name,
                "language": env["language"],
                "version": env["version"],
                "status": health.status,
                "errors": health.errors,
                "suggestions": health.suggestions,
                "fix_attempted": False,
                "snapshot_available": False,
            }
            if health.status == "broken":
                result["fix_attempted"] = True
                snap = snap_repo.get_latest(env["id"])
                if snap:
                    result["snapshot_available"] = True
                    result["snapshot_version"] = snap["version"]
            results.append(result)
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
