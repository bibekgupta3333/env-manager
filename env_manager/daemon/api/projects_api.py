"""REST API — project endpoints."""

from fastapi import APIRouter, HTTPException

from env_manager.cli.db_utils import get_db_path
from env_manager.storage.database import get_connection
from env_manager.storage.repo_project import ProjectRepository

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("/")
async def list_projects():
    conn = get_connection(get_db_path())
    repo = ProjectRepository(conn)
    projects = repo.list_all()
    return {"projects": [dict(p) for p in projects], "count": len(projects)}


@router.get("/{project_id}")
async def get_project(project_id: int):
    conn = get_connection(get_db_path())
    repo = ProjectRepository(conn)
    proj = repo.get_by_id(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return dict(proj)
