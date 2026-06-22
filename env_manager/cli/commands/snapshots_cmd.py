"""Snapshot commands — list and prune environment snapshots."""

import json

import typer

from env_manager.cli.db_utils import ensure_db_dir, get_db_path
from env_manager.storage.database import (
    close_connection,
    get_connection,
    init_db,
)
from env_manager.storage.repo_env import EnvironmentRepository
from env_manager.storage.repo_snapshot import SnapshotRepository

app = typer.Typer(help="Manage environment snapshots")


@app.callback(invoke_without_command=True)
def snapshots(
    project: str = typer.Argument(None, help="Filter by project name"),
) -> None:
    """List available snapshots."""
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        repo = SnapshotRepository(conn)
        all_snaps = repo.list_all()

        if project:
            all_snaps = [
                s for s in all_snaps if project in str(s.get("language", ""))
            ]

        if not all_snaps:
            typer.echo("no snapshots found")
            return

        for snap in all_snaps:
            snap_dict = dict(snap)
            deps = json.loads(snap_dict.get("frozen_deps", "{}"))
            typer.echo(
                f"  v{snap_dict['version']:3d}  "
                f"{snap_dict.get('language', '?'):8s}  "
                f"{len(deps):3d} pkgs  "
                f"{snap_dict.get('created_at', '?')}"
            )
    finally:
        conn.close()
        close_connection(db_path)


@app.command()
def prune(
    project: str = typer.Argument(None, help="Project name (omit for all)"),
    keep: int = typer.Option(
        5, "--keep", "-k", help="Number of versions to keep"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be pruned"
    ),
    confirm: bool = typer.Option(False, "--confirm", help="Confirm pruning"),
) -> None:
    """Delete old snapshot versions beyond --keep most recent."""
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    if not dry_run and not confirm:
        typer.echo("Use --confirm to execute, or --dry-run to preview")
        raise typer.Exit(1)

    try:
        repo = SnapshotRepository(conn)
        env_repo = EnvironmentRepository(conn)

        if project:
            env = env_repo.get_by_path(project)
            if not env:
                typer.echo(f"environment not found: {project}")
                raise typer.Exit(1)
            env_ids = [env["id"]]
        else:
            envs = env_repo.list_all()
            env_ids = [e["id"] for e in envs]

        total_pruned = 0
        for eid in env_ids:
            if dry_run:
                versions = repo.list_by_env(eid)
                to_prune = max(0, len(versions) - keep)
                if to_prune > 0:
                    typer.echo(
                        f"  Would prune {to_prune} versions from env #{eid}"
                    )
            else:
                pruned = repo.prune(eid, keep=keep)
                total_pruned += pruned

        if not dry_run:
            typer.echo(
                f"Pruned {total_pruned} old snapshots (keeping {keep} per env)"
            )
    finally:
        conn.close()
        close_connection(db_path)
