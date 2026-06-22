"""Scan command — discover environments."""

from pathlib import Path

import typer

from env_manager.adapters.registry import AdapterRegistry
from env_manager.cli.db_utils import ensure_db_dir, get_db_path
from env_manager.discovery.scanner import Scanner
from env_manager.storage.database import (
    close_connection,
    get_connection,
    init_db,
)

app = typer.Typer()

DEFAULT_SCAN_PATHS = [str(Path.home() / "projects"), str(Path.home() / "work")]
_PATH_OPTION = typer.Option(None, "--path", "-p", help="Paths to scan")
_DEPTH_OPTION = typer.Option(5, "--depth", "-d", help="Max directory depth")


@app.callback(invoke_without_command=True)
def scan(
    path: list[str] = _PATH_OPTION,
    depth: int = _DEPTH_OPTION,
    incremental: bool = typer.Option(
        False,
        "--incremental",
        "-i",
        help="Only scan directories changed since last scan",
    ),
) -> None:
    """Discover all language environments."""
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        registry = AdapterRegistry(conn)
        adapters = registry.get_all_enabled()

        if not adapters:
            typer.echo("no adapters enabled")
            typer.echo("enable one: envs plugins enable python.venv")
            raise typer.Exit(1)

        scan_paths = path if path else DEFAULT_SCAN_PATHS
        scanner = Scanner(conn, adapters)

        for p in scan_paths:
            resolved = str(Path(p).expanduser())
            if incremental:
                typer.echo(f"Incremental scan of {resolved}...")
            else:
                typer.echo(f"Scanning {resolved}...")
            results = scanner.scan(
                resolved, depth=depth, incremental=incremental
            )
            typer.echo(f"  Found {len(results)} environments")
    finally:
        conn.close()
        close_connection(db_path)
