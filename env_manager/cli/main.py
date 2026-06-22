"""CLI entry point."""

import typer

from env_manager.cli.commands import (
    cleanup_cmd,
    config,
    db_cmd,
    doctor_cmd,
    hook_cmd,
    info,
    lifecycle,
    list_cmd,
    pin_cmd,
    plugin,
    scan,
    snapshots_cmd,
    track_cmd,
    versions_cmd,
)
from env_manager.cli.commands.pin_cmd import toggle_pin

app = typer.Typer(
    name="envs",
    help="Cross-language virtual environment manager",
    no_args_is_help=True,
)

app.add_typer(scan.app, name="scan")
app.add_typer(list_cmd.app, name="list")
app.add_typer(info.app, name="info")
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


# Register unpin as a top-level alias
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
