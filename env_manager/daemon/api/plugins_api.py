"""REST API — plugin endpoints."""

from fastapi import APIRouter, HTTPException

from env_manager.adapters.registry import AdapterRegistry
from env_manager.cli.db_utils import get_db_path
from env_manager.storage.database import get_connection

router = APIRouter(prefix="/api/plugins", tags=["plugins"])


@router.get("/")
async def list_plugins():
    conn = get_connection(get_db_path())
    registry = AdapterRegistry(conn)
    adapters = registry.list_all()
    return {"plugins": adapters, "count": len(adapters)}


@router.post("/{name}/enable")
async def enable_plugin(name: str):
    conn = get_connection(get_db_path())
    registry = AdapterRegistry(conn)
    if registry.enable(name):
        return {"status": "enabled", "name": name}
    raise HTTPException(status_code=404, detail="Adapter not found")


@router.post("/{name}/disable")
async def disable_plugin(name: str):
    conn = get_connection(get_db_path())
    registry = AdapterRegistry(conn)
    if registry.disable(name):
        return {"status": "disabled", "name": name}
    raise HTTPException(status_code=404, detail="Adapter not found")
