"""CLI entry point."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from pathlib import Path

import typer

from env_manager.cli.commands import (
    cleanup_cmd,
    config,
    daemon_cmd,
    db_cmd,
    doctor_cmd,
    hook_cmd,
    lifecycle,
    list_cmd,
    pin_cmd,
    plugin,
    scan,
    snapshots_cmd,
    track_cmd,
    versions_cmd,
)
from env_manager.cli.commands import (
    info as info_cmd,
)
from env_manager.cli.commands.pin_cmd import toggle_pin
from env_manager.cli.db_utils import ensure_db_dir, get_db_path
from env_manager.models.states import DiscoveryStatus
from env_manager.storage.database import (
    close_connection,
    get_connection,
    init_db,
)
from env_manager.storage.repo_env import EnvironmentRepository

app = typer.Typer(
    name="envs",
    help="Cross-language virtual environment manager",
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        try:
            ver = _pkg_version("env-manager")
        except PackageNotFoundError:
            ver = "0.1.0"
        typer.echo(f"envs {ver}")
        raise typer.Exit()


@app.callback()
def _main_callback(
    _ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        help="Show version and exit",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    pass


app.add_typer(scan.app, name="scan")
app.add_typer(list_cmd.app, name="list")
app.command(name="info")(info_cmd.info)
app.add_typer(plugin.app, name="plugins")
app.add_typer(config.app, name="config")
app.add_typer(
    lifecycle.app,
    name="lifecycle",
    help="Create, install, update, delete, restore environments",
)
app.add_typer(doctor_cmd.app, name="doctor")
app.add_typer(snapshots_cmd.app, name="snapshots")
app.add_typer(cleanup_cmd.app, name="cleanup")
app.add_typer(hook_cmd.app, name="hook")
app.add_typer(db_cmd.app, name="db")
app.add_typer(versions_cmd.app, name="versions")
app.add_typer(pin_cmd.app, name="pin")
app.add_typer(track_cmd.app, name="track")
app.add_typer(daemon_cmd.app, name="daemon")


@app.command(name="ignore")
def ignore_cmd(
    path: str = typer.Argument(..., help="Path to exclude"),
) -> None:
    """Exclude a path from all tracking."""
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        repo = EnvironmentRepository(conn)
        resolved = str(Path(path).resolve())
        existing = repo.get_by_path(resolved)
        if existing:
            repo.update_discovery_status(
                existing["id"], DiscoveryStatus.IGNORED
            )
            typer.echo(f"ignored: {resolved}")
        else:
            typer.echo(f"path not tracked: {resolved}")
    finally:
        conn.close()
        close_connection(db_path)


@app.command(name="unpin")
def unpin_cmd(
    project: str = typer.Argument(..., help="Project to unpin"),
) -> None:
    """Unpin a project."""
    toggle_pin(project, False)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
