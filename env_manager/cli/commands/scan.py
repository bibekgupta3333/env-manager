"""Scan command — discover environments."""

import shutil
from pathlib import Path

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn

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
        for p in scan_paths:
            resolved = str(Path(p).expanduser())
            if not Path(resolved).exists():
                typer.echo(
                    f"Warning: scan path does not exist: {resolved}", err=True
                )
        scanner = Scanner(conn, adapters)

        for p in scan_paths:
            resolved = str(Path(p).expanduser())
            prefix = "Incremental scan" if incremental else "Scanning"
            label = f"{prefix} {resolved}"
            if len(label) > 60:
                label = label[:57] + "..."

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                t = progress.add_task(label, total=None)

                def make_callback(task_id, lbl):
                    def cb(dirs: int, found: int) -> None:
                        max_width = shutil.get_terminal_size().columns - 20
                        desc = f"{lbl} — {dirs} dirs, {found} envs"
                        if len(desc) > max_width:
                            desc = "..." + desc[-(max_width - 3) :]
                        progress.update(task_id, description=desc)

                    return cb

                results = scanner.scan(
                    resolved,
                    depth=depth,
                    incremental=incremental,
                    on_progress=make_callback(t, label),
                )

                progress.update(
                    t,
                    description=(f"{label} — done, {len(results)} envs found"),
                    completed=True,
                )

    finally:
        conn.close()
        close_connection(db_path)
