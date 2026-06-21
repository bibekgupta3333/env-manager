"""Doctor command — health checks for environments."""

from pathlib import Path

import typer

from env_manager.adapters.registry import AdapterRegistry
from env_manager.cli.db_utils import ensure_db_dir, get_db_path
from env_manager.storage.database import (
    close_connection,
    get_connection,
    init_db,
)
from env_manager.storage.repo_env import EnvironmentRepository
from env_manager.storage.repo_project import ProjectRepository

app = typer.Typer(help="Health check for environments")


@app.callback(invoke_without_command=True)
def doctor(
    project: str = typer.Argument(
        None, help="Project name or env path (omit for --all)"
    ),
    all_envs: bool = typer.Option(
        False, "--all", help="Check all tracked environments"
    ),
    fix: bool = typer.Option(
        False, "--fix", help="Attempt to auto-repair broken environments"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be checked/fixed"
    ),
) -> None:
    """Check environment health. Detects broken, degraded, and healthy envs."""
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        env_repo = EnvironmentRepository(conn)
        proj_repo = ProjectRepository(conn)
        registry = AdapterRegistry(conn)

        if all_envs or not project:
            envs = env_repo.list_all()
            envs = [
                e
                for e in envs
                if e["management_state"]
                not in ("purged", "snapshotted", "deleted")
            ]
        else:
            env = _resolve_env(conn, project, env_repo, proj_repo)
            if not env:
                typer.echo(f"Environment not found: {project}")
                raise typer.Exit(1)
            envs = [env]

        if not envs:
            typer.echo("No environments to check.")
            return

        results = {"healthy": 0, "degraded": 0, "broken": 0}

        for env in envs:
            proj = (
                proj_repo.get_by_id(env["project_id"])
                if env["project_id"]
                else None
            )
            proj_name = proj["name"] if proj else env["path"]

            adapter = registry.get(env["adapter"])
            if not adapter:
                typer.echo(
                    f"[dim]{proj_name}:[/dim] no adapter available, skipping"
                )
                continue

            health = adapter.check_health(Path(env["path"]))
            env_repo.update_health(env["id"], health.status)

            status_icon = {
                "healthy": "[green]✓[/green]",
                "degraded": "[yellow]⚠[/yellow]",
                "broken": "[red]✗[/red]",
            }.get(health.status, "?")
            typer.echo(
                f"  {status_icon} {proj_name} "
                f"({env['language']} {env['version']}) "
                f"— {health.status}"
            )

            if health.errors:
                for err in health.errors:
                    typer.echo(f"      [red]{err}[/red]")
            if health.suggestions:
                for sug in health.suggestions:
                    typer.echo(f"      [dim]→ {sug}[/dim]")

            results[health.status] += 1

            if fix and health.status == "broken":
                typer.echo("      Attempting fix...")
                snap_repo = __import__(
                    "env_manager.storage.repo_snapshot",
                    fromlist=["SnapshotRepository"],
                ).SnapshotRepository(conn)
                snap = snap_repo.get_latest(env["id"])
                if snap:
                    typer.echo(
                        f"      Snapshot available "
                        f"(v{snap['version']}). "
                        f"Run: envs lifecycle restore "
                        f"{proj_name}"
                    )
                else:
                    typer.echo(
                        "      No snapshot available. Manual recovery needed."
                    )

        typer.echo(
            f"\n  Summary: {results['healthy']} healthy "
            f"| {results['degraded']} degraded "
            f"| {results['broken']} broken"
        )
    finally:
        conn.close()
        close_connection(db_path)


def _resolve_env(conn, identifier, env_repo, proj_repo):
    env = env_repo.get_by_path(identifier)
    if env:
        return env
    proj = proj_repo.get_by_path(identifier)
    if not proj:
        all_projects = proj_repo.list_all()
        proj = next((p for p in all_projects if p["name"] == identifier), None)
    if proj:
        envs = env_repo.list_by_project(proj["id"])
        if envs:
            return envs[0]
    return None
