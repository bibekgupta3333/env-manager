"""Info command — show detailed environment info."""

from pathlib import Path

import typer

from env_manager.cli.db_utils import ensure_db_dir, get_db_path
from env_manager.cli.formatters import format_env_info
from env_manager.models.types import EnvRowDict
from env_manager.storage.database import get_connection, init_db
from env_manager.storage.repo_env import EnvironmentRepository
from env_manager.storage.repo_project import ProjectRepository

app = typer.Typer()


@app.callback(invoke_without_command=True)
def info(
    project: str = typer.Argument(..., help="Project name or path"),
    json_output: bool = typer.Option(
        False, "--json", help="Output in JSON format (for scripting)"
    ),
) -> None:
    """Show detailed info for a project."""
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    proj_repo = ProjectRepository(conn)
    env_repo = EnvironmentRepository(conn)

    # Resolve symlinks for macOS /tmp → /private/tmp
    resolved = str(Path(project).resolve())

    proj = proj_repo.get_by_path(resolved)
    if not proj:
        proj = proj_repo.get_by_path(project)
    if not proj:
        all_projects = proj_repo.list_all()
        proj = next(
            (p for p in all_projects if p["name"] == project), None
        )

    if not proj:
        typer.echo(f"project not found: {project}")
        conn.close()
        raise typer.Exit(1)

    envs = env_repo.list_by_project(proj["id"])
    for env in envs:
        env_dict: EnvRowDict = dict(env)  # type: ignore[assignment]
        env_dict["project_name"] = proj["name"]
        format_env_info(env_dict, json_output=json_output)

    conn.close()
