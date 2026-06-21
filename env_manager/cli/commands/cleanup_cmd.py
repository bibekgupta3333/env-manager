"""Cleanup commands — batch stale/orphaned environment cleanup."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

from env_manager.adapters.registry import AdapterRegistry
from env_manager.cli.db_utils import ensure_db_dir, get_db_path
from env_manager.models.states import ManagementState
from env_manager.storage.database import (
    close_connection,
    get_connection,
    init_db,
)
from env_manager.storage.repo_activity import ActivityRepository
from env_manager.storage.repo_env import EnvironmentRepository
from env_manager.storage.repo_project import ProjectRepository
from env_manager.storage.repo_snapshot import SnapshotRepository

app = typer.Typer(help="Clean up stale and orphaned environments")


@app.callback(invoke_without_command=True)
def cleanup(
    stale_days: int = typer.Option(
        60, "--stale", "-s", help="Days since last use to consider stale"
    ),
    orphaned: bool = typer.Option(
        False, "--orphaned", help="Clean up orphaned environments"
    ),
    snapshot: bool = typer.Option(
        False, "--snapshot", help="Save blueprint before deleting"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview without making changes"
    ),
    confirm: bool = typer.Option(False, "--confirm", help="Execute cleanup"),
) -> None:
    """Batch cleanup of stale and orphaned environments."""
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    if not dry_run and not confirm:
        typer.echo("Use --confirm to execute, or --dry-run to preview")
        raise typer.Exit(1)

    try:
        env_repo = EnvironmentRepository(conn)
        proj_repo = ProjectRepository(conn)
        snap_repo = SnapshotRepository(conn)
        activity_repo = ActivityRepository(conn)
        registry = AdapterRegistry(conn)

        # Gather candidates
        candidates: list[dict[str, Any]] = []
        if stale_days > 0:
            stale_envs = env_repo.list_stale(days=stale_days)
            candidates.extend(dict(e) for e in stale_envs)

        if orphaned:
            orphan_envs = env_repo.list_orphaned()
            candidates.extend(dict(e) for e in orphan_envs)

        # Filter out pinned projects
        filtered = []
        for env in candidates:
            if env.get("project_id"):
                proj = proj_repo.get_by_id(env["project_id"])
                if proj and proj["is_pinned"]:
                    continue
            filtered.append(env)
        candidates = filtered

        if not candidates:
            typer.echo("No environments to clean up.")
            return

        total_size = sum(e.get("size_bytes", 0) for e in candidates)

        if dry_run:
            typer.echo(f"Would process {len(candidates)} environments:")
            action = "snapshot + delete" if snapshot else "delete"
            for env in candidates:
                proj = (
                    proj_repo.get_by_id(env["project_id"])
                    if env.get("project_id")
                    else None
                )
                name = proj["name"] if proj else env["path"]
                size_bytes = env.get("size_bytes", 0) or 0
                typer.echo(
                    f"  {action}: {name} "
                    f"({_fmt_size(size_bytes)})"
                )
            typer.echo(f"Would free: {_fmt_size(total_size)}")
            return

        processed = 0
        freed = 0
        for env in candidates:
            if snapshot:
                adapter = registry.get(env["adapter"])
                if adapter:
                    try:
                        freeze_result = adapter.freeze(Path(env["path"]))
                        snap_repo.insert(
                            env_id=env["id"],
                            frozen_deps={
                                p.name: p.version
                                for p in freeze_result.packages
                            },
                            raw_lockfile=freeze_result.raw_content,
                            lockfile_format=freeze_result.format,
                        )
                    except Exception:
                        pass

            env_repo.update_state(
                env["id"],
                (
                    ManagementState.SNAPSHOTTED
                    if snapshot
                    else ManagementState.DELETED
                ),
            )
            activity_repo.log(
                event="cleaned_up",
                env_id=env["id"],
                detail={"freed_bytes": env.get("size_bytes", 0)},
            )

            # Remove directory
            env_path = Path(env["path"])
            if env_path.exists():
                import shutil

                shutil.rmtree(env_path, ignore_errors=True)

            processed += 1
            freed += env.get("size_bytes", 0)

        typer.echo(
            f"Processed {processed} environments. Freed {_fmt_size(freed)}."
        )
    finally:
        conn.close()
        close_connection(db_path)


@app.command()
def gc(
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview without making changes"
    ),
    confirm: bool = typer.Option(
        False, "--confirm", help="Execute garbage collection"
    ),
) -> None:
    """Purge all soft-deleted environments permanently."""
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    if not dry_run and not confirm:
        typer.echo("Use --confirm to execute, or --dry-run to preview")
        raise typer.Exit(1)

    try:
        env_repo = EnvironmentRepository(conn)
        deleted = env_repo.list_by_state(ManagementState.DELETED)
        snapshotted = env_repo.list_by_state(ManagementState.SNAPSHOTTED)
        all_deleted = list(deleted) + list(snapshotted)

        if dry_run:
            total = sum(e["size_bytes"] for e in all_deleted)
            typer.echo(
                f"Would purge {len(all_deleted)} "
                f"environments ({_fmt_size(total)})"
            )
            return

        for env in all_deleted:
            env_repo.update_state(env["id"], ManagementState.PURGED)

        typer.echo(f"Purged {len(all_deleted)} environments.")
    finally:
        conn.close()
        close_connection(db_path)


@app.command()
def compare(
    project_a: str = typer.Argument(..., help="First project"),
    project_b: str = typer.Argument(..., help="Second project"),
) -> None:
    """Compare packages between two environments."""
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        env_repo = EnvironmentRepository(conn)
        proj_repo = ProjectRepository(conn)
        registry = AdapterRegistry(conn)

        def _get_packages(identifier: str) -> tuple[Any, dict[str, Any]]:
            env = env_repo.get_by_path(identifier)
            if not env:
                proj = next(
                    (
                        p
                        for p in proj_repo.list_all()
                        if p["name"] == identifier
                    ),
                    None,
                )
                if proj:
                    envs = env_repo.list_by_project(proj["id"])
                    env = envs[0] if envs else None
            if not env:
                return None, {}
            adapter = registry.get(env["adapter"])
            if not adapter:
                return env, {}
            pkgs = {
                p.name: p.version
                for p in adapter.get_packages(Path(env["path"]))
            }
            return env, pkgs

        env_a, pkgs_a = _get_packages(project_a)
        env_b, pkgs_b = _get_packages(project_b)

        if not env_a or not env_b:
            typer.echo("One or both environments not found.")
            raise typer.Exit(1)

        only_a = {k: v for k, v in pkgs_a.items() if k not in pkgs_b}
        only_b = {k: v for k, v in pkgs_b.items() if k not in pkgs_a}
        different = {
            k: (pkgs_a[k], pkgs_b[k])
            for k in pkgs_a
            if k in pkgs_b and pkgs_a[k] != pkgs_b[k]
        }

        typer.echo(
            f"[bold]{project_a}[/bold] ({len(pkgs_a)} pkgs) "
            f"←→ [bold]{project_b}[/bold] ({len(pkgs_b)} pkgs)"
        )
        typer.echo()

        if only_a:
            typer.echo(f"[yellow]Only in {project_a}:[/yellow]")
            for k, v in sorted(only_a.items()):
                typer.echo(f"  {k}=={v}")
        if only_b:
            typer.echo(f"[cyan]Only in {project_b}:[/cyan]")
            for k, v in sorted(only_b.items()):
                typer.echo(f"  {k}=={v}")
        if different:
            typer.echo("[magenta]Different versions:[/magenta]")
            for k, (va, vb) in sorted(different.items()):
                typer.echo(f"  {k}: {va} → {vb}")

        if not only_a and not only_b and not different:
            typer.echo("[green]Environments are identical.[/green]")
    finally:
        conn.close()
        close_connection(db_path)


def _fmt_size(size_bytes: int) -> str:
    if size_bytes >= 1_000_000_000:
        return f"{size_bytes / 1_000_000_000:.1f} GB"
    if size_bytes >= 1_000_000:
        return f"{size_bytes / 1_000_000:.1f} MB"
    if size_bytes >= 1_000:
        return f"{size_bytes / 1_000:.1f} KB"
    return f"{size_bytes} B"
