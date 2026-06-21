"""Plugin commands — manage language adapters."""

import typer

from env_manager.adapters.registry import AdapterRegistry
from env_manager.cli.db_utils import ensure_db_dir, get_db_path
from env_manager.storage.database import get_connection, init_db

app = typer.Typer()


@app.command("list")
def list_plugins() -> None:
    """List installed adapters."""
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    registry = AdapterRegistry(conn)
    adapters = registry.list_all()

    for a in adapters:
        status = "enabled" if a["enabled"] else "disabled"
        typer.echo(f"  {a['name']:24s} {a['display_name']:30s} [{status}]")

    conn.close()


@app.command("enable")
def enable_plugin(
    name: str = typer.Argument(..., help="Adapter name")
) -> None:
    """Enable a language adapter."""
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    registry = AdapterRegistry(conn)
    if registry.enable(name):
        typer.echo(f"Enabled: {name}")
    else:
        typer.echo(f"Adapter not found: {name}")
        conn.close()
        raise typer.Exit(1)

    conn.close()


@app.command("disable")
def disable_plugin(
    name: str = typer.Argument(..., help="Adapter name")
) -> None:
    """Disable a language adapter. Its environments won't be scanned."""
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    registry = AdapterRegistry(conn)
    if registry.disable(name):
        typer.echo(f"Disabled: {name}")
    else:
        typer.echo(f"Adapter not found or already disabled: {name}")
        conn.close()
        raise typer.Exit(1)

    conn.close()
