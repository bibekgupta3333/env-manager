"""Daemon core — FastAPI server + lifecycle manager."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from env_manager.cli.db_utils import ensure_db_dir, get_db_path
from env_manager.daemon.api import (
    envs_api,
    health_api,
    plugins_api,
    projects_api,
    snapshots_api,
    ws_api,
)
from env_manager.daemon.scheduler import start_scheduler, stop_scheduler
from env_manager.storage.database import get_connection, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_db_dir()
    init_db(get_db_path())
    start_scheduler(get_db_path())
    yield
    stop_scheduler()
    conn = get_connection(get_db_path())
    conn.close()


app = FastAPI(
    title="env-manager",
    description="Cross-language virtual environment manager API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(envs_api.router)
app.include_router(projects_api.router)
app.include_router(health_api.router)
app.include_router(snapshots_api.router)
app.include_router(plugins_api.router)
app.include_router(ws_api.router)


@app.get("/api/status")
async def status():
    return {"status": "ok", "version": "0.1.0"}
