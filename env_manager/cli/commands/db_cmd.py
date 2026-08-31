"""Database commands — backup, restore, repair the SQLite database."""

import json
import shutil
from datetime import datetime
from pathlib import Path

import typer

from env_manager.adapters.registry import AdapterRegistry
from env_manager.cli.db_utils import ensure_db_dir, get_db_path
from env_manager.storage.database import (
    close_connection,
    get_connection,
    init_db,
)

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
        typer.echo(f"database not found: {db_path_str}")
        typer.echo("run 'envs scan' first to create it")
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
            "use --confirm to restore; "
            "this will overwrite your current database"
        )
        raise typer.Exit(1)

    backup = Path(backup_path)
    if not backup.exists():
        typer.echo(f"backup not found: {backup_path}")
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


@app.command()
def repair() -> None:
    """Rebuild database from filesystem — repair stale or corrupted entries."""
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        registry = AdapterRegistry(conn)

        rows = conn.execute(
            "SELECT id, adapter, path, language, tool FROM environments"
        ).fetchall()

        repaired = 0
        removed = 0
        skipped = 0

        for row in rows:
            env_id = row["id"]
            env_path_str = row["path"]
            adapter_name = row["adapter"]
            language = row["language"]
            tool_name = row["tool"]

            env_path = Path(env_path_str)

            if not env_path.exists():
                conn.execute(
                    "DELETE FROM environments WHERE id = ?", (env_id,)
                )
                conn.commit()
                typer.echo(f"  Removed: {env_path_str}")
                removed += 1
                continue

            adapter = registry.get(adapter_name)
            if adapter is None and language and tool_name:
                adapter = registry.get(f"{language}.{tool_name}")

            if adapter is None:
                typer.echo(
                    f"  Skipped: {env_path_str} "
                    f"(no adapter '{adapter_name}')"
                )
                skipped += 1
                continue

            try:
                meta = adapter.detect(env_path)
                if meta is None:
                    typer.echo(
                        f"  Skipped: {env_path_str} "
                        f"(not detected by {adapter_name})"
                    )
                    skipped += 1
                    continue

                conn.execute(
                    """UPDATE environments
                       SET version = ?, size_bytes = ?,
                           metadata = ?, last_scanned_at = datetime('now')
                       WHERE id = ?""",
                    (
                        meta.version,
                        meta.size_bytes,
                        json.dumps(
                            {"interpreter_path": meta.interpreter_path}
                        ),
                        env_id,
                    ),
                )
                conn.commit()
                typer.echo(f"  Repaired: {env_path_str}")
                repaired += 1
            except Exception as e:
                typer.echo(f"  Error: {env_path_str}: {e}")

        typer.echo()
        typer.echo(
            f"Summary: {repaired} repaired, "
            f"{removed} removed, {skipped} skipped"
        )
    finally:
        conn.close()
        close_connection(db_path)


def _fmt(size_bytes: int) -> str:
    if size_bytes >= 1_000_000:
        return f"{size_bytes / 1_000_000:.1f} MB"
    if size_bytes >= 1_000:
        return f"{size_bytes / 1_000:.1f} KB"
    return f"{size_bytes} B"
