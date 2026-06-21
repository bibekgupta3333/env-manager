"""REST API — environment endpoints."""

from fastapi import APIRouter, HTTPException

from env_manager.cli.db_utils import get_db_path
from env_manager.storage.database import get_connection
from env_manager.storage.repo_env import EnvironmentRepository
from env_manager.storage.repo_project import ProjectRepository

router = APIRouter(prefix="/api/envs", tags=["environments"])


@router.get("/")
async def list_envs(language: str | None = None, state: str | None = None):
    conn = get_connection(get_db_path())
    repo = EnvironmentRepository(conn)
    proj_repo = ProjectRepository(conn)

    envs = repo.list_by_language(language) if language else repo.list_all()

    result = []
    for env in envs:
        env_dict = dict(env)
        if env["project_id"]:
            proj = proj_repo.get_by_id(env["project_id"])
            env_dict["project_name"] = proj["name"] if proj else None
        result.append(env_dict)

    return {"environments": result, "count": len(result)}


@router.get("/{env_id}")
async def get_env(env_id: int):
    conn = get_connection(get_db_path())
    repo = EnvironmentRepository(conn)
    env = repo.get_by_id(env_id)
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    return dict(env)
