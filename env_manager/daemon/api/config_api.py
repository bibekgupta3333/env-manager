"""REST API — config endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from env_manager.cli.db_utils import get_db_path
from env_manager.storage.database import get_connection

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("")
async def get_config():
    conn = get_connection(get_db_path())
    try:
        rows = conn.execute(
            "SELECT name, display_name, enabled "
            "FROM adapter_registry ORDER BY name"
        ).fetchall()
        return {
            "db_path": get_db_path(),
            "adapters": [dict(r) for r in rows],
        }
    finally:
        conn.close()
