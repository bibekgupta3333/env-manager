"""REST API — database endpoints."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from env_manager.cli.db_utils import get_db_path
from env_manager.storage.database import close_connection, get_connection

router = APIRouter(prefix="/api/db", tags=["database"])


@router.post("/backup")
async def backup_db(body: dict[str, Any] | None = None):
    output = (body or {}).get("path")
    db_path_str = get_db_path()
    src = Path(db_path_str)
    if not src.exists():
        msg = f"database not found: {db_path_str}"
        raise HTTPException(status_code=400, detail=msg)
    if output:
        dest = Path(output)
    else:
        backup_dir = Path.home() / ".env-manager" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        dest = backup_dir / f"envs-{timestamp}.db"
    shutil.copy2(src, dest)
    size = dest.stat().st_size
    return {"status": "ok", "path": str(dest), "size_bytes": size}


@router.post("/restore")
async def restore_db(body: dict[str, Any] | None = None):
    backup_path = (body or {}).get("path", "")
    if not backup_path:
        raise HTTPException(status_code=400, detail="path is required")
    backup = Path(backup_path)
    if not backup.exists():
        msg = f"backup not found: {backup_path}"
        raise HTTPException(status_code=400, detail=msg)
    db_path_str = get_db_path()
    src = Path(db_path_str)
    if src.exists():
        shutil.copy2(db_path_str, str(src) + ".pre-restore.bak")
    close_connection(db_path_str)
    shutil.copy2(backup, src)
    return {
        "status": "ok",
        "restored_from": backup_path,
        "note": "original backed up to .pre-restore.bak",
    }


@router.get("/path")
async def db_path_endpoint():
    return {"path": get_db_path()}


@router.post("/repair")
async def repair_db():
    db_path_str = get_db_path()
    conn = get_connection(db_path_str)
    try:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()
        quick_check = conn.execute("PRAGMA quick_check").fetchone()
        conn.execute("REINDEX")
        conn.commit()
        return {
            "status": "ok",
            "integrity_check": integrity[0] if integrity else "ok",
            "quick_check": quick_check[0] if quick_check else "ok",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
