"""Database commands — backup and restore the SQLite database."""

import shutil
from datetime import datetime
from pathlib import Path

import typer

from env_manager.cli.db_utils import get_db_path

app = typer.Typer(help="Backup and restore the env-manager database")


@app.command()
def backup(
    output: str = typer.Option(
        None, "--path", "-p", help="Backup destination path"
    ),
) -> None:
    """Backup the database to a safe location."""
    db_path_str = get_db_path()
    src = Path(db_path_str)

    if not src.exists():
        typer.echo(f"Database not found: {db_path_str}")
        typer.echo("Run envs scan first to create it.")
        raise typer.Exit(1)

    if output:
        dest = Path(output)
    else:
        backup_dir = Path.home() / ".env-manager" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        dest = backup_dir / f"envs-{timestamp}.db"

    shutil.copy2(src, dest)
    size = dest.stat().st_size
    typer.echo(f"Backed up to: {dest} ({_fmt(size)})")


@app.command()
def restore(
    backup_path: str = typer.Argument(..., help="Path to backup file"),
    confirm: bool = typer.Option(
        False, "--confirm", help="Confirm restore (overwrites current DB)"
    ),
) -> None:
    """Restore database from a backup."""
    if not confirm:
        typer.echo(
            "Use --confirm to restore. "
            "This will overwrite your current database."
        )
        raise typer.Exit(1)

    backup = Path(backup_path)
    if not backup.exists():
        typer.echo(f"Backup not found: {backup_path}")
        raise typer.Exit(1)

    db_path_str = get_db_path()
    src = Path(db_path_str)
    if src.exists():
        shutil.copy2(db_path_str, str(src) + ".pre-restore.bak")
        typer.echo(f"Current DB backed up to: {db_path_str}.pre-restore.bak")

    shutil.copy2(backup, src)
    typer.echo(f"Restored from: {backup_path}")


@app.command()
def path() -> None:
    """Show the database file path."""
    typer.echo(get_db_path())


def _fmt(size_bytes: int) -> str:
    if size_bytes >= 1_000_000:
        return f"{size_bytes / 1_000_000:.1f} MB"
    if size_bytes >= 1_000:
        return f"{size_bytes / 1_000:.1f} KB"
    return f"{size_bytes} B"
