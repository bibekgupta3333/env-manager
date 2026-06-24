"""Daemon core — FastAPI server + lifecycle manager."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from env_manager.cli.db_utils import ensure_db_dir, get_db_path
from env_manager.daemon.api import (
    actions_api,
    cleanup_api,
    config_api,
    db_api,
    doctor_api,
    envs_api,
    health_api,
    plugins_api,
    projects_api,
    scan_api,
    snapshots_api,
    track_api,
    ws_api,
)
from env_manager.daemon.scheduler import start_scheduler, stop_scheduler
from env_manager.storage.database import init_db

DASHBOARD_DIR = Path(__file__).parent.parent / "dashboard" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_db_dir()
    init_db(get_db_path())
    start_scheduler(get_db_path())
    yield
    stop_scheduler()


app = FastAPI(
    title="env-manager",
    description="Cross-language virtual environment manager API",
    version="0.1.0",
    lifespan=lifespan,
)

# API routes first
app.include_router(actions_api.router)
app.include_router(cleanup_api.router)
app.include_router(config_api.router)
app.include_router(db_api.router)
app.include_router(doctor_api.router)
app.include_router(envs_api.router)
app.include_router(projects_api.router)
app.include_router(health_api.router)
app.include_router(scan_api.router)
app.include_router(snapshots_api.router)
app.include_router(plugins_api.router)
app.include_router(track_api.router)
app.include_router(ws_api.router)


@app.get("/api/status")
async def status():
    return {"status": "ok", "version": "0.1.0"}


# Serve dashboard index at root, static assets at /assets/
assets_dir = DASHBOARD_DIR / "assets"
if DASHBOARD_DIR.exists() and assets_dir.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=str(assets_dir)),
        name="assets",
    )


@app.get("/favicon.svg")
async def favicon():
    svg = DASHBOARD_DIR / "favicon.svg"
    if svg.exists():
        return FileResponse(svg, media_type="image/svg+xml")
    return Response(status_code=404)


@app.get("/")
async def dashboard():
    index = DASHBOARD_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"message": "Dashboard not available"}
