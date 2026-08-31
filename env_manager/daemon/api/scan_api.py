"""REST API — scan endpoint."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from env_manager.adapters.registry import AdapterRegistry
from env_manager.cli.db_utils import get_db_path
from env_manager.discovery.scanner import Scanner
from env_manager.storage.database import get_connection

router = APIRouter(prefix="/api/scan", tags=["scan"])


@router.post("")
async def scan(body: dict[str, Any]):
    paths = body.get("path", [])
    depth = body.get("depth", 5)
    incremental = body.get("incremental", False)
    if not paths:
        paths = [
            str(__import__("pathlib").Path.home() / "projects"),
            str(__import__("pathlib").Path.home() / "work"),
        ]
    conn = get_connection(get_db_path())
    try:
        registry = AdapterRegistry(conn)
        adapters = registry.get_all_enabled()
        if not adapters:
            raise HTTPException(status_code=400, detail="no adapters enabled")
        scanner = Scanner(conn, adapters)
        all_results = []
        for p in paths:
            results = scanner.scan(p, depth=depth, incremental=incremental)
            all_results.extend(results)
        return {
            "status": "ok",
            "count": len(all_results),
            "environments": [
                {
                    "path": r.path,
                    "language": r.language,
                    "tool": r.tool,
                    "version": r.version,
                }
                for r in all_results
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
