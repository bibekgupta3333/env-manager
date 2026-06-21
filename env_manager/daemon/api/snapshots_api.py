"""REST API — snapshot endpoints."""

from fastapi import APIRouter, HTTPException

from env_manager.cli.db_utils import get_db_path
from env_manager.storage.database import get_connection
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
