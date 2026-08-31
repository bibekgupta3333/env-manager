"""Config command — show current configuration."""

import typer

from env_manager.cli.db_utils import ensure_db_dir, get_db_path
from env_manager.storage.database import get_connection, init_db

app = typer.Typer()


@app.command("show")
def config_show() -> None:
    """Show current configuration."""
    ensure_db_dir()
    db_path = get_db_path()
    typer.echo(f"Database: {db_path}")

    init_db(db_path)
    conn = get_connection(db_path)

    rows = conn.execute(
        "SELECT name, display_name, enabled "
        "FROM adapter_registry ORDER BY name"
    ).fetchall()

    typer.echo("\nLanguage adapters:")
    for row in rows:
        status = "enabled" if row["enabled"] else "disabled"
        typer.echo(f"  {row['name']:24s} [{status}]")

    conn.close()
