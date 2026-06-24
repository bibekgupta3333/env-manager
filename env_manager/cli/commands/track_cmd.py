"""Track/Ignore commands — manually manage environment registration."""

from pathlib import Path

import typer

from env_manager.adapters.registry import AdapterRegistry
from env_manager.cli.db_utils import ensure_db_dir, get_db_path
from env_manager.models.states import DiscoveryStatus
from env_manager.storage.database import (
    close_connection,
    get_connection,
    init_db,
)
from env_manager.storage.repo_env import EnvironmentRepository
from env_manager.storage.repo_project import ProjectRepository

app = typer.Typer(help="Manually register or ignore environment paths")


@app.callback(invoke_without_command=True)
def track(
    path: str = typer.Argument(..., help="Path to register for tracking"),
) -> None:
    """Manually register a path for environment tracking."""
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        env_repo = EnvironmentRepository(conn)
        proj_repo = ProjectRepository(conn)
        registry = AdapterRegistry(conn)

        resolved = str(Path(path).resolve())
        existing = env_repo.get_by_path(resolved)
        if existing:
            env_repo.update_discovery_status(
                existing["id"], DiscoveryStatus.TRACKED
            )
            typer.echo(f"Now tracking: {resolved}")
            return

        # Try to detect what this is
        adapters = registry.get_all_enabled()
        for adapter in adapters:
            meta = adapter.detect(Path(resolved))
            if meta:
                proj_dir = (
                    Path(resolved).parent
                    if adapter.env_type == "project"
                    else Path(resolved)
                )
                proj_id, _ = proj_repo.get_or_create(
                    name=proj_dir.name, path=str(proj_dir.resolve())
                )
                env_repo.insert(
                    project_id=proj_id,
                    adapter=adapter.name,
                    env_type=adapter.env_type,
                    path=resolved,
                    language=meta.language,
                    version=meta.version,
                    tool=meta.tool,
                    size_bytes=meta.size_bytes,
                    discovery_status=DiscoveryStatus.TRACKED,
                )
                typer.echo(f"Tracked: {resolved} ({adapter.name})")
                return

        typer.echo(f"could not detect environment type at: {resolved}")
        typer.echo("Try: envs scan --path " + str(Path(resolved).parent))
        raise typer.Exit(1)
    finally:
        conn.close()
        close_connection(db_path)


@app.command()
def ignore(
    path: str = typer.Argument(..., help="Path to exclude from all tracking"),
) -> None:
    """Exclude a path from all tracking and scanning."""
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        env_repo = EnvironmentRepository(conn)
        resolved = str(Path(path).resolve())

        existing = env_repo.get_by_path(resolved)
        if existing:
            env_repo.update_discovery_status(
                existing["id"], DiscoveryStatus.IGNORED
            )
            typer.echo(f"Ignored: {resolved}")
        else:
            # Register as ignored even if not previously tracked
            typer.echo(
                f"Path not tracked, but will be ignored in future scans: {resolved}"
            )
    finally:
        conn.close()
        close_connection(db_path)
